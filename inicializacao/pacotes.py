"""Instalação inicial e reutilização das dependências na venv."""
import hashlib
import subprocess
from inicializacao.ambiente import RAIZ, AMBIENTE, executar_comando


def verificar_pip(python):
    """Confira se o instalador funciona.

    Args:
        python (Path): Executável validado da venv.

    Raises:
        subprocess.CalledProcessError: Se o pip estiver ausente ou quebrado.
    """
    executar_comando(python, ['-I', '-m', 'pip', '--version'], capturar=True)


def garantir_pip(python):
    """Recupere o pip usando os componentes incluídos no Python.

    Args:
        python (Path): Executável validado da venv.

    Raises:
        subprocess.CalledProcessError: Se a recuperação falhar.
    """
    try:
        verificar_pip(python)
    except subprocess.CalledProcessError:
        print('Recuperando o pip do ambiente virtual...', flush=True)
        executar_comando(python, ['-I', '-m', 'ensurepip', '--upgrade', '--default-pip'])
        verificar_pip(python)


def assinatura(python):
    """Identifique os requisitos, o Python e os pacotes instalados.

    Args:
        python (Path): Executável do ambiente virtual.

    Returns:
        str: Resumo usado para reconhecer um ambiente já preparado.
    """
    codigo = ('import sys; from importlib.metadata import distributions; '
              'print(sys.version); print(sorted((d.metadata["Name"], d.version) for d in distributions()))')
    resultado = executar_comando(python, ['-I', '-c', codigo], capturar=True)
    conteudo = (RAIZ / 'requirements.txt').read_bytes() + b'\0' + resultado.stdout
    return hashlib.sha256(conteudo).hexdigest()


def preparar_pacotes(python):
    """Reutilize a instalação conferida ou prepare os requisitos modificados.

    Args:
        python (Path): Executável da venv.

    Raises:
        OSError: Se o registro não puder ser lido ou gravado.
        subprocess.CalledProcessError: Se a instalação falhar.
    """
    garantir_pip(python)
    registro = AMBIENTE / '.requisitos-verificados'
    try:
        if registro.read_text(encoding='ascii') == assinatura(python):
            return
    except (FileNotFoundError, UnicodeError):
        pass
    instalar_pacotes(python)
    registro.write_text(assinatura(python), encoding='ascii')


def instalar_pacotes(python):
    """Instale os requisitos e confira os conflitos antes de abrir o programa.

    Args:
        python (Path): Executável da venv.

    Raises:
        subprocess.CalledProcessError: Se o pip recusar a instalação ou encontrar conflitos.
    """
    print('Preparando as dependências do projeto...', flush=True)
    executar_comando(python, ['-I', '-m', 'pip', '--isolated', '--disable-pip-version-check',
                             'install', '-r', str(RAIZ / 'requirements.txt')])
    executar_comando(python, ['-I', '-m', 'pip', '--isolated', 'check'])
