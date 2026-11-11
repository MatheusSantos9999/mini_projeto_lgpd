"""Rotinas de atividades para a atividade de exportação LGPD."""
from lgpd.monitoramento.tempo import medir_tempo
from lgpd.exportacao.arquivos import escrever_csv
from lgpd.protecao.mascaramento import mascarar_registro
from lgpd.dados.repositorio import anos_nascimento, registros_identificados, registros_por_ano
from lgpd.dados.esquema import CABECALHOS_IDENTIFICADOS, CABECALHOS_MASCARADOS


@medir_tempo
def exportar_por_ano(conexao, destino, ano_escolhido=None, *, registrador):
    """Exporte os registros mascarados em um CSV para cada ano de nascimento.

    Args:
        conexao: Conexão ativa do SQLAlchemy.
        destino: Diretório que recebe os arquivos.
        ano_escolhido: Ano opcional; a atividade três não usa esse filtro.
        registrador: Registrador de eventos desta execução.

    Returns:
        int: Quantidade de registros exportados após o mascaramento.
    """
    quantidade = 0
    for ano in anos_nascimento(conexao, ano_escolhido):
        linhas = map(mascarar_registro, registros_por_ano(conexao, ano))
        quantidade += escrever_csv(destino / 'mascarados' / f'{ano}.csv', CABECALHOS_MASCARADOS, linhas)
    return quantidade


@medir_tempo
def exportar_identificados(conexao, destino, ano_escolhido=None, *, registrador):
    """Exporte todos os nomes e CPFs originais para a atividade três.

    Args:
        conexao: Conexão ativa do SQLAlchemy.
        destino: Diretório que recebe os arquivos.
        ano_escolhido: Ano opcional; a atividade três não usa esse filtro.
        registrador: Registrador de eventos desta execução.

    Returns:
        int: Quantidade de nomes e CPFs exportados sem máscara.
    """
    linhas = registros_identificados(conexao)
    return escrever_csv(destino / 'identificados' / 'todos.csv', CABECALHOS_IDENTIFICADOS, linhas)


def executar_atividades(conexao, destino, atividade, ano_escolhido, registrador):
    """Execute as atividades escolhidas sem modificar os registros de origem.

    Args:
        conexao: Conexão ativa do SQLAlchemy.
        destino: Diretório que recebe os arquivos.
        atividade: Seleção entre atividade 2, atividade 3 ou todas.
        ano_escolhido: Ano opcional; a atividade três não usa esse filtro.
        registrador: Registrador de eventos desta execução.

    Returns:
        dict[str, int]: Contagem por operação executada.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    opcoes = {'2': (exportar_por_ano,), '3': (exportar_identificados,), 'todas': (exportar_por_ano, exportar_identificados)}
    try:
        funcoes = opcoes[atividade]
    except KeyError:
        raise ValueError('Escolha a atividade 2, 3 ou todas.') from None
    return {funcao.__name__: funcao(conexao, destino, ano_escolhido, registrador=registrador) for funcao in funcoes}
