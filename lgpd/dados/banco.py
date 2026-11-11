"""Rotinas de banco para a atividade de exportação LGPD."""
from contextlib import contextmanager
from getpass import getpass
from sqlalchemy import URL, create_engine
from lgpd.protecao.validacao import texto_obrigatorio, validar_porta


def ler_endereco_banco():
    """Solicite a conexão e a senha sem registrar credenciais no código ou no log.

    Returns:
        sqlalchemy.URL: Campos de conexão com caracteres escapados.

    Raises:
        ValueError: Se host, porta, banco, usuário ou senha forem inválidos.
    """
    host = texto_obrigatorio(input('Host: ').strip(), 'host')
    porta = validar_porta(input('Porta [5432]: ').strip() or '5432')
    banco = texto_obrigatorio(input('Banco: ').strip(), 'banco')
    usuario = texto_obrigatorio(input('Usuário: ').strip(), 'usuário')
    senha = texto_obrigatorio(getpass('Senha: '), 'senha')
    return URL.create('postgresql+psycopg2', username=usuario, password=senha, host=host, port=porta, database=banco)


def criar_conexao_postgres(opcoes):
    """Configure TLS, tempo limite e leitura consistente no PostgreSQL.

    Args:
        opcoes: Opções validadas do programa.

    Returns:
        sqlalchemy.Engine: Conexão configurada, ainda sem consulta.
    """
    return create_engine(
        ler_endereco_banco(), hide_parameters=True, echo=False,
        isolation_level='REPEATABLE READ', pool_pre_ping=True,
        connect_args={'connect_timeout': 10, 'sslmode': opcoes.modo_ssl},
    )


@contextmanager
def abrir_postgres(opcoes):
    """Abra uma transação somente de leitura, sem criar ou alterar tabelas.

    Args:
        opcoes: Opções validadas do programa.

    Yields:
        sqlalchemy.Connection: Transação somente de leitura no banco existente.
    """
    motor = criar_conexao_postgres(opcoes)
    try:
        with motor.connect() as conexao, conexao.begin():
            conexao.exec_driver_sql('SET TRANSACTION READ ONLY')
            conexao.exec_driver_sql("SET LOCAL statement_timeout = '60s'")
            yield conexao
    finally:
        motor.dispose()
