"""Rotinas de demonstracao para a atividade de exportação LGPD."""
from contextlib import contextmanager
from datetime import date, datetime
from sqlalchemy import create_engine
from lgpd.dados.esquema import METADADOS, USUARIOS


def registros_demonstracao():
    """Crie registros fictícios para demonstrar a exportação sem banco externo.

    Returns:
        list[dict]: Três registros fictícios em dois anos diferentes.
    """
    nomes = ('Pessoa Exemplo', 'Pessoa Amostra', 'Pessoa Teste')
    return [registro_demonstracao(indice, nome, 1990 + indice % 2) for indice, nome in enumerate(nomes, 1)]


def registro_demonstracao(identificador, nome, ano):
    """Monte um registro fictício com CPF deliberadamente inválido.

    Args:
        identificador: Identificador do registro fictício.
        nome: Nome fictício ou campo descritivo.
        ano: Ano válido do calendário.

    Returns:
        dict: Campos compatíveis com a tabela usuarios.
    """
    instante = datetime(2025, 1, 1, 12, 0)
    return dict(id=identificador, nome=nome, cpf='000.000.000-00',
                email=f'pessoa{identificador}@example.invalid', telefone='+55 (011) 9000-0000',
                data_nascimento=date(ano, 8, 24), created_on=instante, updated_on=instante)


@contextmanager
def abrir_demonstracao(opcoes=None):
    """Abra um SQLite isolado em memória com os registros de demonstração.

    Args:
        opcoes: Opções validadas do programa.

    Yields:
        sqlalchemy.Connection: SQLite isolado com registros fictícios.
    """
    motor = create_engine('sqlite://')
    try:
        with motor.begin() as conexao:
            METADADOS.create_all(conexao)
            conexao.execute(USUARIOS.insert(), registros_demonstracao())
            yield conexao
    finally:
        motor.dispose()
