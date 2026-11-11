"""Criação e verificação de um ambiente virtual exclusivo do projeto."""
import os
from pathlib import Path
import subprocess
import venv

RAIZ = Path(__file__).resolve().parents[1]
AMBIENTE = RAIZ / '.venv'


def python_virtual():
    """Localize o Python da venv.

    Returns:
        Path: Executável esperado no Windows, Linux ou macOS.
    """
    relativos = {'nt': 'Scripts/python.exe', 'posix': 'bin/python'}
    return AMBIENTE / relativos[os.name]


def preparar_ambiente():
    """Crie a venv ausente e confira a versão e o isolamento.

    Returns:
        Path: Executável validado do ambiente virtual.

    Raises:
        OSError: Se o ambiente não puder ser criado.
        subprocess.CalledProcessError: Se o Python não for compatível.
    """
    python = python_virtual()
    try:
        python.stat()
    except FileNotFoundError:
        print('Criando o ambiente virtual...', flush=True)
        venv.EnvBuilder(with_pip=True).create(AMBIENTE)
    verificar_ambiente(python)
    return python


def verificar_ambiente(python):
    """Confira a versão mínima e a localização do ambiente.

    Args:
        python (Path): Executável da venv.

    Raises:
        subprocess.CalledProcessError: Se o ambiente estiver inválido.
    """
    codigo = ('import sys; from pathlib import Path; '
              'valido = sys.version_info >= (3, 10) and sys.prefix != sys.base_prefix '
              'and Path(sys.prefix).resolve() == Path(sys.argv[1]).resolve(); '
              'sys.exit(0 if valido else "Ambiente inválido. Use Python 3.10 ou superior.")')
    executar_comando(python, ['-I', '-c', codigo, str(AMBIENTE)])


def ambiente_execucao(python):
    """Isole as variáveis usadas pelos subprocessos.

    Args:
        python (Path): Executável do ambiente virtual.

    Returns:
        dict: Variáveis com a venv ativa e sem caminhos Python externos.
    """
    ambiente = dict(os.environ, VIRTUAL_ENV=str(AMBIENTE), PYTHONNOUSERSITE='1')
    ambiente.pop('PYTHONPATH', None)
    ambiente.pop('PYTHONHOME', None)
    ambiente['PATH'] = str(python.parent) + os.pathsep + ambiente.get('PATH', '')
    return ambiente


def executar_comando(python, argumentos, capturar=False):
    """Execute um comando pelo Python da venv, sem interpretação pelo shell.

    Args:
        python (Path): Executável do ambiente virtual.
        argumentos (list[str]): Argumentos separados do comando.
        capturar (bool): Indica se a saída deve ser capturada.

    Returns:
        subprocess.CompletedProcess: Resultado da execução.

    Raises:
        subprocess.CalledProcessError: Se o comando falhar.
    """
    return subprocess.run([str(python), *argumentos], cwd=RAIZ,
                          env=ambiente_execucao(python), check=True, capture_output=capturar)
