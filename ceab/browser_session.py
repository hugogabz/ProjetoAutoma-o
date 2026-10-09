"""Chrome/Chromium do sistema com perfil persistente, sem porta CDP pública."""
import os
import shutil
from pathlib import Path


def find_browser():
    candidates = [shutil.which(name) for name in ('google-chrome','google-chrome-stable','chrome','chromium','chromium-browser')]
    candidates += ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                   os.path.expandvars(r'%PROGRAMFILES%\Google\Chrome\Application\chrome.exe'),
                   os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe')]
    return next((str(Path(path).resolve()) for path in candidates if path and Path(path).is_file()),None)


def open_persistent(playwright,config):
    profile = Path(config['profile_path'])
    profile.mkdir(parents=True,exist_ok=True,mode=0o700)
    options = {'headless':bool(config['headless']),'args':['--disable-popup-blocking','--restore-last-session']}
    if config.get('executable_path'): options['executable_path'] = config['executable_path']
    context = playwright.chromium.launch_persistent_context(str(profile),**options)
    page = context.pages[0] if context.pages else context.new_page()
    from playwright.sync_api import Error as BrowserError
    try: page.goto(config['start_url'],wait_until='domcontentloaded',timeout=30000)
    except BrowserError:
        # Falha de rede ou espera por certificado não deve destruir a janela
        # antes que a pessoa possa fazer login/navegar manualmente.
        pass
    return context
