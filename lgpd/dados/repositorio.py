"""Rotinas de repositorio para a atividade de exportação LGPD."""
from sqlalchemy import extract, select
from lgpd.dados.esquema import USUARIOS
from lgpd.protecao.validacao import validar_ano


def anos_nascimento(conexao, ano_escolhido=None):
    """Selecione os anos existentes ou o ano solicitado pelo operador.

    Args:
        conexao: Conexão ativa do SQLAlchemy.
        ano_escolhido: Ano opcional; a atividade três não usa esse filtro.

    Returns:
        tuple[int, ...]: Anos existentes ou o ano selecionado.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    seletores = {type(None): todos_anos_nascimento, int: ano_selecionado}
    try:
        seletor = seletores[type(ano_escolhido)]
    except KeyError:
        raise ValueError('O ano selecionado deve ser inteiro ou None.') from None
    return seletor(conexao, ano_escolhido)


def ano_selecionado(conexao, ano):
    """Retorne o ano solicitado mesmo quando não há registros correspondentes.

    Args:
        conexao: Conexão ativa do SQLAlchemy.
        ano: Ano válido do calendário.

    Returns:
        tuple[int]: Único ano solicitado, mesmo que não existam registros.
    """
    return (validar_ano(ano),)


def todos_anos_nascimento(conexao, ignorado=None):
    """Liste os anos de nascimento existentes em ordem crescente.

    Args:
        conexao: Conexão ativa do SQLAlchemy.
        ignorado: Argumento reservado para a interface comum.

    Returns:
        tuple[int, ...]: Anos existentes em ordem crescente.
    """
    ano = extract('year', USUARIOS.c.data_nascimento)
    consulta = select(ano).distinct().order_by(ano)
    with conexao.execute(consulta) as resultado:
        return tuple((validar_ano(valor) for valor in resultado.scalars()))


def registros_por_ano(conexao, ano):
    """Percorra os registros do ano sem carregar toda a tabela na memória.

    Args:
        conexao: Conexão ativa do SQLAlchemy.
        ano: Ano válido do calendário.

    Yields:
        sqlalchemy.Row: Registro do ano solicitado, na ordem das colunas.
    """
    # O SQLAlchemy envia o ano como parâmetro, separado do SQL.
    consulta = select(USUARIOS).where(extract('year', USUARIOS.c.data_nascimento) == validar_ano(ano))
    with conexao.execute(consulta.order_by(USUARIOS.c.id).execution_options(yield_per=500)) as resultado:
        yield from resultado


def registros_identificados(conexao):
    """Percorra todos os nomes e CPFs originais, em ordem de identificador.

    Args:
        conexao: Conexão ativa do SQLAlchemy.

    Yields:
        sqlalchemy.Row: Nome e CPF originais, ordenados pelo identificador.
    """
    consulta = select(USUARIOS.c.nome, USUARIOS.c.cpf).order_by(USUARIOS.c.id)
    with conexao.execute(consulta.execution_options(yield_per=500)) as resultado:
        yield from resultado
