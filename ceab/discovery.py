"""Descoberta read-only de abas já abertas por CDP local, sem Playwright."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
from .launcher import validate_cdp
from .rules import normalize
import urllib.request


def _argument(arguments, name):
    for index, argument in enumerate(arguments):
        if argument.startswith(name+'='):
            return argument.split('=',1)[1]
        if argument == name and index+1 < len(arguments):
            return arguments[index+1]
    return None


def running_browser_urls(proc_root=Path('/proc')):
    """Linux: ler somente argumentos de navegadores do próprio usuário.

    DevToolsActivePort é consultado apenas no perfil indicado pelo processo,
    para uma porta dinâmica (0). Não lê cookies, histórico ou credenciais.
    """
    urls = set()
    if not proc_root.is_dir() or not hasattr(os,'getuid'):
        return urls
    for process in proc_root.iterdir():
        if not process.name.isdigit(): continue
        try:
            if process.stat().st_uid != os.getuid(): continue
            name = (process/'comm').read_text().strip().lower()
            if not any(browser in name for browser in ('brave','chrome','chromium')): continue
            args = (process/'cmdline').read_bytes().decode(errors='replace').split('\0')
            # Processos auxiliares não são servidores CDP independentes.
            if _argument(args,'--type'): continue
            port = _argument(args,'--remote-debugging-port')
            if port == '0':
                profile = _argument(args,'--user-data-dir')
                if not profile: continue
                with (Path(profile)/'DevToolsActivePort').open() as metadata:
                    port = metadata.readline(16).strip()
            if port and port.isdigit() and 0 < int(port) <= 65535:
                urls.add(f'http://127.0.0.1:{int(port)}')
        except (OSError,ValueError):
            continue
    return urls


def _local_json(endpoint,path):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(endpoint+path,timeout=1) as response:
        content = response.read(2_000_001)
    if len(content)>2_000_000: raise ValueError('Resposta CDP excede o limite.')
    return json.loads(content)


def inspect_browser(endpoint):
    """Retorna títulos, nunca cookies, URLs de processo ou websocket de sessão."""
    try:
        endpoint = validate_cdp(endpoint)
        version = _local_json(endpoint,'/json/version')
        if not isinstance(version,dict) or not version.get('webSocketDebuggerUrl'): return None
        targets = _local_json(endpoint,'/json/list')
        if not isinstance(targets,list): return None
        tabs = []
        for target in targets:
            if not isinstance(target,dict) or target.get('type') != 'page': continue
            title = str(target.get('title',''))
            host = urlparse(str(target.get('url',''))).hostname or ''
            queue = 'LISTA DE PROCESSOS POR LOCALIZADOR' in normalize(title)
            eproc = 'eproc' in host.lower() and (host.lower().endswith('.trf6.jus.br') or host.lower()=='trf6.jus.br')
            if eproc or queue:
                tabs.append({'title':title[:200] or 'eproc TRF6','queue':queue})
        if not tabs: return None
        return {'endpoint':endpoint,'browser':str(version.get('Browser','Chromium'))[:100],'tabs':tabs}
    except (OSError,ValueError,TypeError):
        return None


def find_existing_browsers(cdp_urls=None):
    """Não inicia navegador nem cria abas. Sonda portas declaradas/conhecidas."""
    candidates = sorted(running_browser_urls() | {'http://127.0.0.1:9222','http://127.0.0.1:9223'}) if cdp_urls is None else list(cdp_urls)
    candidates = list(dict.fromkeys(candidates))[:32]
    if not candidates: return []
    with ThreadPoolExecutor(max_workers=min(8,len(candidates))) as pool:
        results = [result for result in pool.map(inspect_browser,candidates) if result]
    return sorted(results,key=lambda result:(not any(tab['queue'] for tab in result['tabs']),result['endpoint']))
