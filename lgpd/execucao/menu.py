"""Escolhas interativas para executar o projeto sem argumentos de comando."""
from argparse import Namespace
from pathlib import Path
import sys
from lgpd.execucao.argumentos import ler_argumentos
from lgpd.execucao.entrada import ano_opcional, ler_escolha, ler_valor

MENU_ORIGEM = ('\n1 - Demonstração com dados incluídos\n'
               '2 - Configurar conexão PostgreSQL\n0 - Sair\n'
               'Escolha a origem [Enter = 1]: ')
MENU_ATIVIDADE = ('\n1 - Atividade 2: exportar dados mascarados por ano\n'
                  '2 - Atividade 3: exportar nomes e CPFs originais\n'
                  '3 - Executar as duas atividades\nEscolha a atividade [Enter = 3]: ')
MENU_TLS = ('\n1 - Validar certificado e host do PostgreSQL (verify-full)\n'
            '2 - Exigir criptografia sem validar a identidade (require)\n'
            'Escolha o modo TLS [Enter = 1]: ')


def selecionar_opcoes(argumentos=None):
    """Abra o menu na execução comum ou leia os argumentos opcionais.

    Args:
        argumentos (list[str] | None): Argumentos recebidos; None lê o terminal.

    Returns:
        argparse.Namespace | None: Configuração escolhida ou pedido para sair.
    """
    recebidos = sys.argv[1:] if argumentos is None else list(argumentos)
    if recebidos:
        return ler_argumentos(recebidos)
    return abrir_menu()


def abrir_menu():
    """Solicite as escolhas necessárias antes de abrir a origem dos dados.

    Returns:
        argparse.Namespace | None: Opções da execução ou pedido para sair.
    """
    print('Atividade LGPD — escolha como executar o projeto.')
    origem = ler_escolha(MENU_ORIGEM, {'1': True, '2': False, '0': None})
    if origem is None:
        return None
    atividade = ler_escolha(MENU_ATIVIDADE, {'1': '2', '2': '3', '3': 'todas'}, '3')
    ano = selecionar_ano(atividade)
    saida = ler_valor('Pasta dos arquivos [Enter = saida]: ', Path, 'saida')
    modo_ssl = selecionar_tls(origem)
    return Namespace(demonstracao=origem, atividade=atividade, ano=ano, saida=saida, modo_ssl=modo_ssl)


def selecionar_ano(atividade):
    """Solicite o ano somente quando a atividade utiliza esse filtro.

    Args:
        atividade (str): Atividade 2, atividade 3 ou todas.

    Returns:
        int | None: Ano escolhido ou ausência de filtro.
    """
    if atividade == '3':
        return None
    return ler_valor('Ano para a atividade 2 [Enter = todos]: ', ano_opcional)


def selecionar_tls(demonstracao):
    """Solicite a configuração TLS somente para o PostgreSQL externo.

    Args:
        demonstracao (bool): Indica o uso dos dados fictícios incluídos.

    Returns:
        str: Modo TLS escolhido; não é utilizado pela demonstração.
    """
    if demonstracao:
        return 'verify-full'
    return ler_escolha(MENU_TLS, {'1': 'verify-full', '2': 'require'})
