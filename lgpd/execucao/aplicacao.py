"""Rotinas de aplicacao para a atividade de exportação LGPD."""
import sys
from sqlalchemy.exc import SQLAlchemyError
from lgpd.exportacao.atividades import executar_atividades
from lgpd.execucao.menu import selecionar_opcoes
from lgpd.dados.banco import abrir_postgres
from lgpd.dados.demonstracao import abrir_demonstracao
from lgpd.exportacao.arquivos import criar_diretorio_execucao, exportacoes_temporarias
from lgpd.monitoramento.registros import registro_execucao


def executar_exportacao(opcoes):
    """Prepare o log e publique as exportações quando o lote terminar.

    Args:
        opcoes: Opções validadas do programa.

    Returns:
        tuple: Diretório da execução e contagens por atividade.
    """
    diretorio = criar_diretorio_execucao(opcoes.saida)
    origem = {True: abrir_demonstracao, False: abrir_postgres}[opcoes.demonstracao]
    with registro_execucao(diretorio / 'execucao.log') as registrador:
        with exportacoes_temporarias(diretorio) as temporarios:
            with origem(opcoes) as conexao:
                contagens = executar_atividades(conexao, temporarios, opcoes.atividade, opcoes.ano, registrador)
    return (diretorio, contagens)


def principal(argumentos=None):
    """Execute o programa e apresente falhas sem expor credenciais ou dados.

    Args:
        argumentos: Argumentos opcionais; None lê o terminal.

    Returns:
        int: Zero no sucesso ou código diferente de zero na falha.
    """
    try:
        return executar_configurado(selecionar_opcoes(argumentos))
    except EOFError:
        print('Entrada encerrada. Execute o main.py no terminal integrado do VS Code.', file=sys.stderr)
        return 1
    except (SQLAlchemyError, OSError, ValueError, TypeError, UnicodeError):
        print('Falha na exportação. Confira conexão, TLS, tabela, formatos e permissões de saída.', file=sys.stderr)
        return 1


def executar_configurado(opcoes):
    """Execute as escolhas do operador ou encerre a opção de saída.

    Args:
        opcoes (argparse.Namespace | None): Configuração escolhida no menu ou no terminal.

    Returns:
        int: Zero quando a operação ou o encerramento solicitado termina.
    """
    if opcoes is None:
        print('Programa encerrado.')
        return 0
    apresentar_execucao(opcoes)
    diretorio, contagens = executar_exportacao(opcoes)
    print(f'Concluído: {contagens}. Diretório de saída: {diretorio}')
    return 0


def apresentar_execucao(opcoes):
    """Informe a origem dos dados antes de iniciar as atividades.

    Args:
        opcoes (argparse.Namespace): Opções validadas da execução.
    """
    modos = {True: 'Demonstração: dados fictícios incluídos, sem solicitar conexão.',
             False: 'Configuração PostgreSQL: informe host, porta, banco, usuário e senha.'}
    print(modos[opcoes.demonstracao])
    print('Arquivos mascarados podem permitir identificação. A atividade 3 exporta nomes e CPFs originais.')


if __name__ == '__main__':
    try:
        raise SystemExit(principal())
    except KeyboardInterrupt:
        print('Execução cancelada.', file=sys.stderr)
        raise SystemExit(130) from None
