# mini_projeto_lgpd

Projeto em Python para consultar cadastros de usuários e exportar arquivos CSV, com opções de mascaramento de dados e organização por ano de nascimento.

A aplicação funciona pelo terminal e oferece um menu para escolher a origem dos dados, o tipo de exportação e a pasta dos arquivos. É possível experimentar o fluxo com dados fictícios incluídos ou configurar a conexão com um banco PostgreSQL.

## Funcionalidades

- Exportação de registros mascarados, separados por ano de nascimento.
- Exportação de nomes e CPFs originais em um único arquivo.
- Execução das duas exportações na mesma operação.
- Filtro por ano para os registros mascarados.
- Registro da duração e do resultado das exportações.
- Preparação automática do ambiente virtual e das dependências.

## Como executar

O projeto aceita Python 3.10 ou superior. A versão adotada no projeto é Python 3.15.

1. Baixe ou clone o repositório.
2. Abra no VS Code a pasta que contém `main.py` e `requirements.txt`.
3. Abra `main.py` e selecione **Executar Arquivo Python no Terminal**.
4. Responda às opções exibidas no terminal integrado.

O `main.py` cria a `.venv`, verifica o pip e instala as dependências. A primeira instalação precisa de internet. Nas próximas execuções, o ambiente é reutilizado.

Não é necessário ativar a venv manualmente nem informar argumentos para usar o programa. Quem preferir iniciar pelo terminal pode executar:

```bash
python main.py
```

Use o terminal integrado do VS Code para responder às perguntas. O painel **Saída** não recebe entradas de teclado.

## Modos de execução

| Modo | Funcionamento |
| --- | --- |
| Demonstração com dados incluídos | Cria um SQLite em memória com três registros fictícios. Não solicita host, banco ou senha. |
| Configurar conexão PostgreSQL | Solicita os dados de acesso e consulta uma tabela existente, sem alterar os registros de origem. |

### Demonstração

Para conferir o fluxo completo, escolha a demonstração, selecione as duas exportações, deixe o ano em branco e mantenha a pasta de saída padrão.

Pressionar Enter nas quatro perguntas utiliza essas escolhas. O programa gera os arquivos, informa o caminho no terminal e encerra. Os dados fictícios são recriados em memória a cada execução.

### PostgreSQL

Selecione **Configurar conexão PostgreSQL** no menu. Informe as opções de exportação, o modo TLS e os dados de conexão: host, porta, banco, usuário e senha.

A opção configura o acesso a um servidor existente. Ela não instala o PostgreSQL, não cria o banco e não popula tabelas.

A tabela `usuarios` precisa conter as colunas:

```text
id, nome, cpf, email, telefone, data_nascimento, created_on, updated_on
```

O modo TLS padrão, `verify-full`, verifica certificado e host. A alternativa `require` exige criptografia, mas não oferece a mesma verificação de identidade do servidor.

A senha é solicitada sem exibição no terminal. A conexão utiliza uma transação somente de leitura e tempo limite para as consultas.

## Exportações e mascaramento

A exportação mascarada gera um CSV para cada ano de nascimento encontrado. Quando um ano é informado, somente os registros daquele ano são exportados.

| Campo | Tratamento |
| --- | --- |
| Nome | Preserva a inicial do primeiro nome e os sobrenomes. |
| CPF | Preserva os três primeiros dígitos e substitui os demais por asteriscos. |
| E-mail | Preserva a inicial e o domínio, ocultando o restante antes do arroba. |
| Telefone | Retorna somente os quatro últimos dígitos. |

O identificador e as datas permanecem nos registros mascarados. A validação do CPF verifica o formato, sem calcular os dígitos verificadores.

A exportação identificada contém todos os nomes e CPFs originais. O filtro por ano não se aplica a ela, mesmo quando as duas exportações são executadas juntas.

## Fluxo do código

1. O `main.py` prepara o ambiente e inicia a aplicação com o Python da venv.
2. O menu recebe a origem dos dados, a exportação desejada, o ano e a pasta de saída. Respostas inválidas são solicitadas novamente.
3. A aplicação abre o SQLite de demonstração ou a conexão PostgreSQL.
4. O repositório consulta os registros necessários.
5. As rotinas de proteção validam os valores e aplicam as máscaras na exportação mascarada.
6. Os CSVs são escritos em uma pasta temporária. A pasta final de exportações só é publicada quando todas as operações terminam.
7. O programa informa o resultado, encerra as conexões e libera os recursos utilizados.

Um decorador mede o tempo das exportações e registra sucesso ou falha no log. Se uma exportação falhar, o lote parcial é descartado e a aplicação apresenta uma mensagem no terminal.

## Organização do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `main.py` | Preparar o ambiente e iniciar a aplicação. |
| `inicializacao/` | Criar a venv, recuperar o pip e instalar dependências. |
| `lgpd/execucao/` | Menu, leitura das respostas e coordenação do fluxo. |
| `lgpd/dados/` | Conexões, esquema da tabela, consultas e dados de demonstração. |
| `lgpd/protecao/` | Validação e mascaramento dos valores. |
| `lgpd/exportacao/` | Operações de exportação, escrita e publicação dos CSVs. |
| `lgpd/monitoramento/` | Registro de eventos e medição de tempo. |
| `testes/` | Verificações de exportação, menu, validações e preparação do ambiente. |

As funções e as docstrings estão em português. Os módulos separam a interação com o usuário, o acesso aos dados, as regras de mascaramento e a gravação dos arquivos.

## Arquivos gerados

Por padrão, cada execução cria uma pasta exclusiva dentro de `saida`. Na demonstração completa, são gerados:

- `exportacoes/mascarados/1990.csv`: registros mascarados de 1990.
- `exportacoes/mascarados/1991.csv`: registros mascarados de 1991.
- `exportacoes/identificados/todos.csv`: nomes e CPFs fictícios originais.
- `execucao.log`: operações, resultado e duração.

Os arquivos usam UTF-8 com BOM e campos entre aspas. Valores com prefixos de fórmulas ou caracteres de controle são recusados. Execuções anteriores não são sobrescritas.

## Cuidados com os dados

O projeto demonstra técnicas de mascaramento e cuidados na exportação. Isso não garante anonimização nem conformidade completa com a LGPD: sobrenomes, datas e outros campos preservados ainda podem permitir identificação.

A exportação identificada mantém nomes e CPFs originais. Não publique arquivos com dados de pessoas reais no repositório. O `.gitignore` exclui a venv, os CSVs, os logs e a pasta de saída padrão.

## Testes

Depois da preparação do ambiente, execute os testes pelo Python da venv.

No Windows:

```powershell
.\.venv\Scripts\python.exe -m testes.executar
```

No Linux ou macOS:

```bash
.venv/bin/python -m testes.executar
```

Os testes usam SQLite em memória e verificam o menu, as exportações, as máscaras, o tratamento de falhas e o iniciador. A conexão PostgreSQL é simulada nos testes; o acesso ao servidor e os certificados precisam ser conferidos no ambiente em que serão utilizados.
