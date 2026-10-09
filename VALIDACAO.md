# Validação da implementação

Ambiente testado: Python 3.12, Chromium 151 e dependências de `requirements.lock`.

- `python -m pytest -q`: **65 testes aprovados, nenhum pulado**, com as amostras
  pessoais disponíveis no diretório local ignorado `samples/private/`.
- Novo modo padrão: worker abre navegador gerenciado com perfil persistente,
  espera comando explícito antes de processar e não exige uma porta CDP.
- Cookie de sessão sintético (sem data de expiração), armazenamento local e
  armazenamento da aba (sessionStorage) preservados após fechar e reabrir
  Chromium no mesmo perfil. A aba autenticada é restaurada sem visitar a URL
  inicial de login; a aba vazia adicional do Chrome não é confundida com ela.
- Paginação alterada com recarga para 100; clique no link fornecido abre 100
  abas locais, com 100 números distintos. Seleção parcial não inverte linhas
  previamente marcadas.
- Regressão reproduzida no código anterior: confirmação de abertura cancelada
  automaticamente impedia todas as abas. Agora a confirmação é aceita apenas
  durante o clique de abertura; confirmações posteriores continuam sem aceite.
- Links de abertura repetidos não causam ambiguidade, e o link pode ficar fora
  do frame das linhas. Alertas imediatos ou atrasados e falhas de JavaScript
  são relatados sem aguardar 60 segundos por abas que não abrirão.
- Aba aberta inicialmente em about:blank aguarda navegação atrasada. Worker
  lê a primeira antes de identificar a próxima, registra uma aba com falha
  e continua para a seguinte.
- Execução completa do worker gerenciado, com conferência e envio simulado,
  sem clicar em Intimar ou salvar minuta. Abas permanecem abertas após terminar;
  o comando Encerrar navegador fecha o contexto e mantém o perfil no disco.
- Perfis de demonstração e produção separados por nome do banco.
- Banco antigo migrado sem perder o histórico; proteções contra reenvio mantidas.
- Falha na navegação inicial não destrói a janela antes do login manual.
- Modo avançado CDP continua testado com descoberta read-only de abas e sessão
  existente. O painel padrão não consulta portas nem pede depuração remota.

Também são verificados extração por células e por layout nos dois PDFs reais,
HTML, datas e notas, NB, valores/honorários, regras de destino, preservação dos
campos fora do escopo, máscaras, frames, fila, seleção da proposta mais recente,
aprovação e edição na UI, sessão expirada, pausa/cancelamento, tentativa única
persistente, erros isolados e minuta sem salvar em modo teste.

Os testes de envio efetivo e gravação de minuta atingem somente páginas locais
com dados sintéticos. Nenhuma requisição foi enviada ao eproc real. Certificado,
token, validade da sessão e controles do TRF6 ainda dependem de validação no
computador do usuário, começando em modo teste. Login salvo não impede expiração
ou novas exigências de autenticação pelo eproc.

A abertura de navegador foi exercitada em modo headless neste ambiente de nuvem.
Na operação local, o modo padrão abre uma janela na sessão gráfica do usuário.
A UI foi testada pelo Streamlit AppTest, sem Playwright no processo da UI.

Os PDFs pessoais, bancos, logs, credenciais e perfis de navegador não fazem parte
do pacote de distribuição. Sem os PDFs, seus quatro testes serão pulados;
os demais usam amostras sintéticas versionadas.
