# Validação da implementação

Ambiente testado: Python 3.12, Chromium 151, dependências de `requirements.lock`.

- `python -m pytest -q`: **46 testes aprovados, nenhum pulado**, com as amostras
  pessoais disponíveis no diretório local ignorado `samples/private/`.
- Verificação adicional da UI e do estado após inclusão dos avisos no painel:
  `python -m pytest tests/test_ui.py tests/test_state_worker.py -q`.
- Instalação repetida via `CEAB_VENV_DIR=/workspace/ceab-venv bash scripts/setup.sh`
  concluída sem alterar os arquivos de dependências.
- `python -m pip check`: nenhuma dependência incompatível.
- Streamlit iniciado; endpoint de saúde respondeu `ok`. Chromium renderizou
  o painel sem exceções e com modo teste ligado.

Os testes incluem leitura dos dois PDFs reais (nomes invertidos em relação ao
PRD), extração por células e por layout, datas e notas, NB, valores/honorários,
regras de destino, preservação dos campos fora do escopo, máscara de datas,
frames, seleção das abas e da proposta mais recente, aprovação e edição na UI,
worker separado por CDP, sessão expirada, pausa/cancelamento, tentativa única
persistente, erros isolados e minutar sem salvar em modo teste. Também
verificam a descoberta read-only de abas existentes, portas dinâmicas no Linux,
a recusa de endereços externos e a preservação dos cookies de uma sessão
sintética já aberta. Uma aba de login antiga não impede localizar outra
lista autenticada no mesmo contexto.

Os testes de envio efetivo, diálogos e gravação de minuta atingiram somente
páginas de teste com dados sintéticos. Nenhuma requisição foi enviada ao eproc
real. A sessão autenticada, a seleção de linhas e os controles de minuta do
ambiente TRF6 ainda precisam de validação local pelo usuário, começando em
modo teste.

Os PDFs pessoais, banco SQLite, logs, credenciais e perfil Chromium não fazem
parte do pacote de distribuição. Sem os PDFs, seus quatro testes dependentes
serão pulados; os demais usam dados sintéticos versionados.

A descoberta não habilita CDP num navegador iniciado sem depuração remota.
Não abre um navegador, não instala extensão e não extrai credenciais.

Após melhorar o diagnóstico de conexão do Chrome, os testes afetados foram
executados com `python -m pytest tests/test_discovery.py tests/test_ui.py
tests/test_cdp_integration.py -q`: **11 aprovados**. Incluem distinção entre
porta indisponível e navegador sem aba do eproc, tolerância a URL inválida
em outra aba e integração CDP com sessão sintética existente. O Chrome do
computador do usuário não foi acessado a partir da máquina de nuvem.
