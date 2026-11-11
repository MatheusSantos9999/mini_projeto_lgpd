"""Prepare a venv e abra o menu sem ativação manual do ambiente."""
import subprocess
import sys
from inicializacao.ambiente import preparar_ambiente, executar_comando
from inicializacao.pacotes import preparar_pacotes


def iniciar(argumentos):
    """Prepare o ambiente antes de importar os pacotes usados na atividade.

    Args:
        argumentos (list[str]): Opções encaminhadas ao programa de exportação.

    Raises:
        subprocess.CalledProcessError: Se a preparação ou a atividade falhar.
    """
    python = preparar_ambiente()
    preparar_pacotes(python)
    executar_comando(python, ['-m', 'lgpd.execucao.aplicacao', *argumentos])


def principal(argumentos=None):
    """Inicie o projeto e apresente falhas sem exibir dados de conexão.

    Args:
        argumentos (list[str] | None): Argumentos opcionais; None usa os do terminal.

    Returns:
        int: Zero no sucesso ou um código de erro.
    """
    try:
        iniciar(sys.argv[1:] if argumentos is None else argumentos)
        return 0
    except subprocess.CalledProcessError as erro:
        print('Etapa interrompida. Confira a mensagem acima.', file=sys.stderr)
        return erro.returncode or 1
    except (OSError, ValueError):
        print('Não foi possível preparar o ambiente. Confira o Python e as permissões.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    try:
        raise SystemExit(principal())
    except KeyboardInterrupt:
        print('\nExecução cancelada.', file=sys.stderr)
        raise SystemExit(130) from None
