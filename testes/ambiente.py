"""Teste do iniciador em uma venv real, sem depender da internet."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest import TestCase
from zipfile import ZipFile

CONFERENCIA = TestCase()


def criar_pacote_teste(pasta):
    """Monte um wheel local para testar uma instalação real pelo pip.

    Args:
        pasta (Path): Diretório isolado do teste.

    Returns:
        Path: Arquivo wheel sem dependências externas.
    """
    caminho = pasta / 'componente_exemplo-1.0-py3-none-any.whl'
    with ZipFile(caminho, 'w') as pacote:
        pacote.writestr('componente_exemplo.py', 'valor = 42\n')
        pacote.writestr('componente_exemplo-1.0.dist-info/METADATA', 'Metadata-Version: 2.1\nName: componente-exemplo\nVersion: 1.0\n')
        pacote.writestr('componente_exemplo-1.0.dist-info/WHEEL', 'Wheel-Version: 1.0\nGenerator: teste\nRoot-Is-Purelib: true\nTag: py3-none-any\n')
        pacote.writestr('componente_exemplo-1.0.dist-info/RECORD', 'componente_exemplo.py,,\ncomponente_exemplo-1.0.dist-info/METADATA,,\ncomponente_exemplo-1.0.dist-info/WHEEL,,\ncomponente_exemplo-1.0.dist-info/RECORD,,\n')
    return caminho


def preparar_projeto_teste(pasta):
    """Copie o iniciador real e substitua só a aplicação e os pacotes do ensaio.

    Args:
        pasta (Path): Diretório isolado do teste.
    """
    origem = Path(__file__).resolve().parents[1]
    shutil.copyfile(origem / 'main.py', pasta / 'main.py')
    shutil.copytree(origem / 'inicializacao', pasta / 'inicializacao')
    (pasta / 'lgpd/execucao').mkdir(parents=True)
    (pasta / 'lgpd/__init__.py').write_text('')
    (pasta / 'lgpd/execucao/__init__.py').write_text('')
    (pasta / 'lgpd/execucao/aplicacao.py').write_text('import sys\nfrom pathlib import Path\nimport componente_exemplo\nassert sys.prefix != sys.base_prefix\nassert componente_exemplo.valor == 42\nassert sys.argv[1:] == []\nPath("executou").write_text(sys.prefix)\n')
    pacote = criar_pacote_teste(pasta)
    (pasta / 'requirements.txt').write_text('--no-index\n' + pacote.as_uri() + '\n')


def executar_main_teste(pasta):
    """Execute o main a partir de outra pasta.

    Args:
        pasta (Path): Diretório do projeto de ensaio.

    Returns:
        str: Saída do iniciador e da aplicação de teste.
    """
    resultado = subprocess.run([sys.executable, str(pasta / 'main.py')],
                               cwd=pasta.parent, capture_output=True, text=True, timeout=90)
    CONFERENCIA.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
    return resultado.stdout


def python_do_teste(pasta):
    """Localize o interpretador criado pelo iniciador.

    Args:
        pasta (Path): Diretório do projeto de ensaio.

    Returns:
        Path: Interpretador da venv deste teste.
    """
    return pasta / '.venv' / {'nt': 'Scripts/python.exe', 'posix': 'bin/python'}[os.name]


def conferir_reutilizacao(pasta):
    """Confira que a segunda execução não recria nem reinstala o ambiente.

    Args:
        pasta (Path): Projeto de ensaio já executado uma vez.
    """
    registro = (pasta / '.venv/pyvenv.cfg').read_bytes()
    saida = executar_main_teste(pasta)
    CONFERENCIA.assertNotIn('Criando o ambiente', saida)
    CONFERENCIA.assertNotIn('Preparando as dependências', saida)
    CONFERENCIA.assertEqual((pasta / '.venv/pyvenv.cfg').read_bytes(), registro)


def conferir_recuperacao_pip(pasta):
    """Remova o pip do ensaio e confira sua recuperação automática.

    Args:
        pasta (Path): Projeto de ensaio com ambiente já preparado.
    """
    subprocess.run([str(python_do_teste(pasta)), '-m', 'pip', 'uninstall', '-y', 'pip'],
                   check=True, capture_output=True)
    saida = executar_main_teste(pasta)
    CONFERENCIA.assertIn('Recuperando o pip', saida)
    CONFERENCIA.assertTrue((pasta / 'executou').exists())


def testar_ambiente_real():
    """Crie, reutilize e repare uma venv em pasta com espaços."""
    with tempfile.TemporaryDirectory() as temporario:
        pasta = Path(temporario) / 'atividade com espacos'
        pasta.mkdir()
        preparar_projeto_teste(pasta)
        CONFERENCIA.assertIn('Criando o ambiente', executar_main_teste(pasta))
        CONFERENCIA.assertEqual(Path((pasta / 'executou').read_text()).resolve(), (pasta / '.venv').resolve())
        conferir_reutilizacao(pasta)
        conferir_recuperacao_pip(pasta)
