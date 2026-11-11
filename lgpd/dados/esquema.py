"""Mapeamento da tabela existente; a aplicação não cria tabelas no PostgreSQL."""
from sqlalchemy import Column, Date, DateTime, Integer, MetaData, String, Table

METADADOS = MetaData()
USUARIOS = Table(
    'usuarios', METADADOS,
    Column('id', Integer, primary_key=True),
    Column('nome', String(50), nullable=False),
    Column('cpf', String(14), nullable=False),
    Column('email', String(100), nullable=False),
    Column('telefone', String(20), nullable=False),
    Column('data_nascimento', Date, nullable=False),
    Column('created_on', DateTime),
    Column('updated_on', DateTime),
)
CABECALHOS_MASCARADOS = (
    'id', 'nome', 'cpf', 'email', 'telefone', 'data_nascimento',
    'criado_em', 'atualizado_em',
)
CABECALHOS_IDENTIFICADOS = ('nome', 'cpf')
