# Automação da Requisição CEAB/DJ · eproc TRF6

Painel local para ler propostas de acordo, preencher requisições e submetê-las
**somente após conferência humana**. Implementa o PRD v2 de 08/10/2026.
Modo teste vem ligado: não clica em **Intimar** nem em **Apenas salvar**.

## Instalação

Requer Python 3.11 ou superior e Chrome/Chromium. Tudo é executado no computador
que contém a sessão autenticada do eproc. O navegador aberto no seu computador
não é acessível a um worker em uma máquina de nuvem.

Linux/macOS, na raiz do repositório:

```bash
bash scripts/setup.sh
source .venv/bin/activate
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
```

As dependências diretas estão em `requirements.txt`; `requirements.lock` fixa
as dependências transitivas da instalação testada. Não são necessários tokens
ou APIs do eproc. Não execute o painel em um servidor público.

## Operação: aproveitar a aba já aberta

O painel procura abas do eproc em navegadores que **já estão em execução**.
Não inicia Brave/Chrome, não cria uma janela ou aba de login e não copia cookies.
Não utiliza extensão. O worker assume a Lista de Processos por Localizador
na sessão existente e mantém os critérios de conferência do PRD.

**Limite técnico:** a sessão existente precisa estar acessível por depuração
remota (CDP). Não é possível ativar CDP retroativamente em um Brave aberto
normalmente. Sem esse acesso, o sistema informa que não encontrou uma aba
acessível e não tenta reiniciar o navegador nem recuperar seus cookies.
Versões que restringem a depuração do perfil padrão precisam de um perfil
permitido pelo navegador. O sistema não contorna essa restrição.

1. No Brave/Chrome já aberto com depuração remota, deixe a aba autenticada do
   eproc na **Lista de Processos por Localizador**, com até 25 processos.
2. Com o ambiente Python ativado, execute na raiz do repositório:

   ```bash
   streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
   ```

3. O painel procura a aba automaticamente. Clique em **Procurar aba aberta**
   se abriu o navegador ou mudou de página depois de iniciar o painel. No Linux,
   descobre as portas declaradas pelos processos Brave/Chrome/Chromium do
   próprio usuário, incluindo porta dinâmica indicada em `DevToolsActivePort`.
   Também consulta as portas locais 9222 e 9223. Não varre todas as portas e
   não lê histórico, cookies ou credenciais do perfil.
4. Se houver mais de um navegador acessível, escolha **Navegador encontrado**.
   O painel mostra os títulos das abas. O worker procura a lista nos contextos
   existentes, incluindo uma sessão fora do primeiro contexto. Não abre outra
   aba de lista nem de login. As abas de processos/documentos continuam sendo
   abertas conforme o fluxo de trabalho do PRD.
5. Mantenha **Modo teste** ligado e clique em **Iniciar**. Em **Conferir
   formulário**, revise cada proposta, edite DIB/DIP/DCB se necessário, marque
   **Conferi os dados e autorizo o envio** e clique em **Enviar conferidos**.
6. Em teste, os valores aprovados são reaplicados e lidos de volta. Quando há
   minuta de cálculos, a preferência é conferida numa aba temporária sem salvar.
   Os processos ficam FINALIZADO/Simulado e as abas permanecem abertas.
7. Para envio real, conclua/cancele a simulação, volte à lista existente e inicie
   outra execução, desligando modo teste e confirmando a permissão de envio.
   Simulações podem ser relidas; a aprovação anterior não é reutilizada. O
   worker intima em sequência e só minuta quando o destino exige cálculos.

Se usa outra porta que não foi descoberta, abra **Conexão manual / aba não
encontrada**, marque a opção manual e informe, por exemplo,
`http://localhost:9333`. Somente endereços de loopback são aceitos.

### Quando o navegador ainda não oferece CDP

Isso exige preparação manual antes de usá-lo na automação. Para Brave no Linux,
a opção abaixo utiliza um perfil persistente separado:

```bash
brave-browser --remote-debugging-port=9222 --user-data-dir="$HOME/.ceab-brave" --disable-popup-blocking
```

Use `brave` se esse for o nome do executável. Faça login nesse perfil uma vez e
mantenha sua janela aberta para as execuções seguintes, enquanto a sessão for
válida. Reabrir o mesmo perfil preserva os dados do navegador; o eproc pode
exigir novo login quando a sessão expirar. O painel não executa esse comando.
`scripts/start_browser.py` permanece como utilitário opcional para preparação
e demonstração, com `--executable` para indicar o Brave.

**Pausar** termina a operação do processo atual e aguarda entre processos.
**Cancelar** encerra no próximo limite seguro e preserva as abas restantes.
Não encerre à força o worker durante um envio. Uma sessão expirada pausa o
worker: faça login no navegador e clique em **Retomar**; valores relidos exigem
nova conferência.

Um erro de processo não bloqueia os demais. O número e o motivo aparecem no
painel, e sua aba fica aberta. Corrija no eproc e clique em **Resolvido
manualmente**, ou em **Ignorar**. MINUTAR_PENDENTE significa que a intimação
já ocorreu e somente a minuta precisa ser resolvida; não reenviar.

## Estado, privacidade e recuperação

- UI (`app.py`) e worker (`worker.py`) são processos separados. A UI não importa
  Playwright. Os comandos e o estado trafegam por SQLite local em
  `runtime/state.db`, com tabelas `execucao`, `processo`, `comando` e `log`.
- `CEAB_STATE_PATH` permite escolher outro banco local. Use bancos distintos
  para demonstrações sintéticas e operação real. Não apague o banco de uma
  operação real para repetir processos: ele contém as proteções de envio.
- Um registro por número de processo; aprovação e reserva de envio são
  transacionais. Uma tentativa real é persistida **antes** de clicar em
  Intimar. Depois de tentativa, crash ou confirmação ambígua, o robô não tenta
  novamente; a pessoa verifica o resultado no eproc. Registros já intimados
  não voltam para a fila.
- Ao cancelar antes do envio, uma nova execução pode reler os processos
  interrompidos sem reutilizar aprovações. Erros permanecem para resolução
  manual. A auditoria anterior permanece no CSV.
- Dados de processo não são enviados a serviços de IA. O documento é baixado
  com os cookies da sessão apenas da mesma origem do eproc, processado em
  memória e sua aba de leitura é fechada. Referências externas são recusadas.
- Auditoria em UTC exportável em CSV; inclui números e dados de benefício.
  Banco, logs, perfil do navegador, backups e exportações são sensíveis e devem
  ficar no computador autorizado. SQLite não é criptografado.
- O painel mostra erros se o CDP não estiver disponível ou a lista não estiver
  aberta. A conexão CDP fica restrita ao endereço HTTP de loopback.
- Um worker morto é detectado no painel. Se uma execução não puder ser
  recuperada, seus registros e eventuais reservas de envio são preservados.

## Demonstração sem eproc

Com o ambiente ativado, execute cada comando em um terminal:

```bash
python -m ceab.demo
python scripts/start_browser.py --url http://127.0.0.1:8765/queue
```

Linux/macOS:

```bash
CEAB_STATE_PATH=runtime/demo.db streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

PowerShell:

```powershell
$env:CEAB_STATE_PATH="runtime/demo.db"
streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

O simulador tem três processos fictícios: um com valor (RPV), um sem valor
(minuta de cálculos) e um tipo desconhecido (erro isolado). O formulário
`samples/formulario.html` reproduz os seletores fornecidos com dados sintéticos
e campos que devem ser preservados. O simulador é servido somente no loopback.

## Testes

```bash
python -m pytest -q
```

Os testes exercitam regras, extração PDF/HTML, máscaras, preservação dos campos
fora de escopo, conferência da UI, fila, envio simulado, confirmação/validação,
minuta, aprovação transacional, pausa/cancelamento, prevenção de reenvio e
worker separado conectado por CDP ao Chromium local. Os cliques de envio real
nos testes atingem exclusivamente o servidor sintético.

Se não houver Chromium do sistema, execute `python -m playwright install
chromium`. `CEAB_TEST_CHROMIUM` pode apontar para outro executável nos testes.

Os PDFs pessoais fornecidos estão em `samples/private/`, ignorados pelo Git.
Em outro checkout, copie-os ali para rodar os testes PDF; sem eles, os testes que dependem deles
são **pulados**, nunca considerados aprovados. Nos anexos recebidos,
`exemplo1.pdf` contém o restabelecimento e `exemplo2.pdf` a concessão, ao contrário
da nomenclatura da tabela do PRD. Os testes respeitam o conteúdo dos anexos.
Há também amostras HTML sintéticas versionadas, sem dados pessoais.

## Limites de validação

O fluxo foi validado em formulário/simulador local e em Chromium por CDP.
Não foi executado contra uma sessão autenticada do eproc TRF6. A seleção de
linhas usa a convenção Infra `input[id^='chkInfraItem']`; confirme-a no ambiente
real. Os seletores de minuta dependem de papel/texto porque não foram mapeados
nos anexos. Ausência ou ambiguidade gera pendência para conferência manual.

O sucesso de envio segue o critério do PRD: Intimar sai da página em até 15 s,
sem alertas de validação. Uma resposta ambígua é encaminhada à pessoa, sem
repetição automática. A data DCB pode ser removida na conferência; somente o
campo DCB que o próprio robô preencheu será limpo antes da reaplicação.

Não altera RMI, CID, início de incapacidade, trânsito em julgado, botões de
opção, prazos, parte ou evento vinculado sugerido. Não faz login, paginação,
OCR, análise de identidade ou chamadas a APIs do eproc.

## Arquivos

- `ceab/extractor.py`, `ceab/rules.py`: extração e regras puras.
- `ceab/state.py`: SQLite, comandos, aprovação e auditoria.
- `ceab/selectors.py`, `ceab/eproc.py`: seletores e automação por etapa.
- `ceab/worker.py`, `worker.py`: execução sequencial por CDP.
- `ceab/discovery.py`: descoberta local de navegadores e abas existentes.
- `ceab/launcher.py`, `app.py`: subprocesso e painel Streamlit.
- `ceab/demo.py`, `samples/`, `tests/`: simulador e validação local.

`selectors.py` fica dentro de `ceab/` para não ocultar o módulo `selectors` da
biblioteca padrão usado por subprocessos.

### Chrome no Linux: diagnóstico de aba não encontrada

O painel agora diferencia conexão CDP indisponível, resposta inválida, falha
na consulta de abas e Chrome conectado sem uma aba reconhecida do eproc.
Uma aba com URL inválida não impede reconhecer as outras.

No mesmo computador que executa o Streamlit, abra no Chrome:
`http://127.0.0.1:9222/json/version`. Se houver erro de conexão, não existe
acesso CDP por esse endereço naquele momento. Confira a porta usada pelo
Chrome. Para preparar uma instância acessível, execute manualmente:

```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.ceab-chrome" --disable-popup-blocking
```

Use `google-chrome-stable` se necessário. Caso esse perfil já esteja aberto
sem depuração, feche as janelas desse perfil antes de executar o comando.
O comando não habilita depuração numa janela pessoal que já está aberta;
as versões atuais do Chrome exigem perfil separado para essa finalidade.
Mantenha o mesmo perfil `.ceab-chrome` nas próximas execuções.

Quando o endereço de diagnóstico mostrar JSON, abra o eproc nesse Chrome,
faça login se necessário, deixe a Lista de Processos por Localizador aberta
 e clique em **Procurar aba aberta**. Chrome e Streamlit precisam estar na
mesma máquina; um Streamlit na nuvem não alcança o Chrome do seu computador
pelo endereço localhost.
