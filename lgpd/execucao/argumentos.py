"""Rotinas de argumentos para a atividade de exportação LGPD."""
import argparse
from pathlib import Path
from lgpd.protecao.validacao import validar_ano


def argumento_ano(valor):
    """Converta o ano informado no terminal e apresente erros de argumento.

    Args:
        valor: Valor recebido para validação.

    Returns:
        int: Ano validado para o calendário.

    Raises:
        argparse.ArgumentTypeError: Se o ano recebido não for válido.
    """
    try:
        return validar_ano(valor)
    except ValueError as erro:
        raise argparse.ArgumentTypeError(str(erro)) from None


def ler_argumentos(argumentos=None):
    """Leia as opções das atividades, da conexão e do diretório de saída.

    Args:
        argumentos: Argumentos opcionais; None lê o terminal.

    Returns:
        argparse.Namespace: Opções validadas da execução.
    """
    analisador = argparse.ArgumentParser(description='Exportações da atividade LGPD; mascaramento não garante anonimato.')
    analisador.add_argument('--atividade', choices=('2', '3', 'todas'), default='todas')
    configurar_origem(analisador)
    analisador.add_argument('--ano', type=argumento_ano, help='Filtre somente a atividade 2; a atividade 3 exporta todos.')
    analisador.add_argument('--saida', type=Path, default=Path('saida'))
    analisador.add_argument('--modo-ssl', choices=('verify-full', 'require'), default='verify-full', help='verify-full confere certificado e host; require exige apenas criptografia TLS.')
    return analisador.parse_args(argumentos)


def configurar_origem(analisador):
    """Use a demonstração por padrão e exija uma opção para acessar PostgreSQL.

    Args:
        analisador (argparse.ArgumentParser): Analisador das opções do terminal.
    """
    origem = analisador.add_mutually_exclusive_group()
    origem.add_argument('--demonstracao', dest='demonstracao', action='store_true',
                        help='Use os dados fictícios incluídos; este é o modo padrão.')
    origem.add_argument('--postgres', dest='demonstracao', action='store_false',
                        help='Configure a conexão PostgreSQL informando os dados de acesso.')
    analisador.set_defaults(demonstracao=True)
