# Atividade LGPD

O projeto exporta registros de uma tabela PostgreSQL sem modificar o banco de origem. A atividade 2 separa os dados por ano de nascimento e aplica as máscaras pedidas. A atividade 3 gera um CSV com todos os nomes e CPFs originais.

## Executar pelo menu

1. Extraia o ZIP.
2. No VS Code, abra a pasta que contém `main.py` e `requirements.txt`.
3. Abra `main.py` e clique em **Executar Arquivo Python no Terminal**. Também é possível usar F5 com a configuração **Executar pelo menu**.
4. Responda às opções que aparecem no terminal integrado.

Não é necessário abrir o CMD, usar outro terminal nem digitar argumentos. A execução comum sempre abre o menu. O `main.py` cria a `.venv` e instala as dependências automaticamente; a primeira instalação precisa de internet. Depois ele reutiliza o ambiente e os pacotes.

O projeto requer Python 3.10 ou superior; Python 3.15 é a versão adotada no trabalho. Se o VS Code solicitar um interpretador, selecione o Python instalado. O painel **Saída** não recebe respostas de teclado: use o terminal integrado para responder ao menu.

### Apresentar com os dados incluídos

No menu, siga estas escolhas:

1. Na origem, escolha **1 — Demonstração com dados incluídos**.
2. Na atividade, escolha **3 — Executar as duas atividades**.
3. No ano, pressione **Enter** para exportar todos os anos.
4. Na pasta de saída, pressione **Enter** para usar `saida`.

Essas são as escolhas padrão: pressionar Enter nas quatro perguntas executa a demonstração completa. Ela usa SQLite em memória com dados fictícios, sem solicitar host, banco ou senha. Escolher **0 — Sair** na primeira pergunta encerra sem exportar.

O resultado aparece no terminal com o caminho completo dos arquivos. Abra a pasta `saida`, depois a pasta `lgpd-...` criada nessa execução. Ela contém:

- `exportacoes/mascarados/1990.csv`: um registro mascarado;
- `exportacoes/mascarados/1991.csv`: dois registros mascarados;
- `exportacoes/identificados/todos.csv`: os três nomes e CPFs fictícios originais;
- `execucao.log`: operações executadas e duração.

Cada execução cria outra pasta, sem sobrescrever a anterior. Não há página no navegador: o programa apresenta as escolhas no terminal, exporta os arquivos e encerra.

### Escolher outra operação

O próprio menu permite selecionar apenas uma atividade, filtrar o ano e alterar a pasta dos arquivos. O ano não é solicitado quando a escolha é somente a atividade 3, pois ela sempre exporta todos os nomes e CPFs. Opções e anos inválidos são perguntados novamente. Ctrl+C cancela a execução.

## PostgreSQL opcional

Na origem do menu, escolha **2 — Configurar conexão PostgreSQL** somente se já tiver o servidor e o banco da atividade. Em seguida, escolha atividade, ano, pasta de saída e modo TLS. Depois o programa solicita os dados de conexão. Esse modo não cria banco nem popula tabelas.

A tabela `usuarios` já deve existir. O programa espera as colunas:

```text
id, nome, cpf, email, telefone, data_nascimento, created_on, updated_on
```

Os nomes `created_on` e `updated_on` foram mantidos no mapeamento para continuar compatível com o banco original. No CSV, os cabeçalhos correspondentes são `criado_em` e `atualizado_em`.

Na opção Configurar conexão PostgreSQL do menu, o programa solicita host, porta, banco, usuário e senha. Para um servidor local, o host costuma ser `localhost` e a porta `5432`; o nome do banco, o usuário e a senha são os que foram configurados no PostgreSQL. A senha é lida com `getpass` e não é gravada no código nem no log. A transação é somente de leitura, usa um retrato consistente dos dados e tem tempo limite para as consultas.

No menu TLS, a opção 1 (`verify-full`) verifica certificado e host e exige uma configuração válida de certificados. A opção 2 (`require`) exige criptografia, mas não oferece a mesma verificação de identidade do servidor. Configure o acesso conforme o banco utilizado.

O filtro por ano vale somente para a atividade 2. A atividade 3 sempre exporta todos os nomes e CPFs, mesmo quando um ano foi informado.

## Máscaras e arquivos

As máscaras preservam a inicial do primeiro nome, os três primeiros dígitos do CPF, a inicial e o domínio do e-mail e os quatro últimos dígitos do telefone. A validação do CPF confere o formato, sem calcular seus dígitos verificadores.

Cada execução cria uma pasta exclusiva dentro de `saida`. Os resultados ficam em:

- `exportacoes/mascarados/1990.csv`: um arquivo para cada ano selecionado ou encontrado;
- `exportacoes/identificados/todos.csv`: nomes e CPFs originais da atividade 3;
- `execucao.log`: nome da operação, situação e duração em segundos.

O CSV usa UTF-8 com BOM e campos entre aspas. Valores com prefixos de fórmula ou caracteres de controle são recusados. O código não altera silenciosamente essas células para concluir a exportação.

Os arquivos são preparados em um diretório temporário. A pasta `exportacoes` só é publicada depois que o lote inteiro termina. Se houver uma falha comum durante a escrita ou leitura, os arquivos parciais são descartados. O log da execução permanece disponível para indicar a etapa que terminou com falha.

## Organização

Os módulos estão agrupados por responsabilidade, com dois a quatro arquivos de implementação em cada subpasta:

- `main.py`: ponto de entrada e chamada da aplicação;
- `inicializacao/`: criação da venv, recuperação do pip e instalação dos pacotes;
- `lgpd/execucao/`: coordenação da exportação e leitura das opções do terminal;
- `lgpd/dados/`: conexão, mapeamento da tabela, consultas e banco de demonstração;
- `lgpd/exportacao/`: atividades, escrita dos CSVs e publicação do lote;
- `lgpd/protecao/`: mascaramento e validação dos valores;
- `lgpd/monitoramento/`: log da execução e medição de tempo;
- `testes/`: casos de transformação, exportação, falhas e preparação do ambiente.

O `main.py` prepara o ambiente e chama `lgpd.execucao.aplicacao`. Esse módulo abre o menu, recebe as escolhas, abre a origem de dados, prepara o log e coordena as exportações. `menu.py` organiza as perguntas, `entrada.py` valida as respostas e `argumentos.py` mantém a alternativa por argumentos para quem preferir. As atividades consultam `dados`, aplicam as regras de `protecao` e gravam os arquivos por meio de `exportacao`. O decorador de tempo registra a duração em `monitoramento`.

As funções e as docstrings estão em português. Os títulos `Args`, `Returns`, `Yields` e `Raises` seguem a convenção das docstrings Google. Os corpos têm no máximo dez linhas físicas, desconsiderando documentação, comentários e linhas vazias. Nomes de bibliotecas, métodos externos e colunas existentes no banco foram preservados.

## Conferir o funcionamento

Depois da preparação do ambiente, no Windows:

```powershell
.\.venv\Scripts\python.exe -m testes.executar
```

No Linux ou macOS:

```bash
.venv/bin/python -m testes.executar
```

Os cenários de exportação usam SQLite em memória. A configuração da transação PostgreSQL é conferida com uma conexão simulada; isso não substitui executar contra o banco e o certificado da instituição. O teste do iniciador cria uma venv temporária e instala um pacote local, sem depender de downloads para esse ensaio.

## Alternativa para automação

Quem preferir ainda pode fornecer argumentos; nesse caso o menu não é aberto. Eles não são necessários para usar o projeto pelo VS Code. Exemplos:

```bash
python main.py --demonstracao --atividade todas
python main.py --postgres --atividade 2 --ano 1990
```
