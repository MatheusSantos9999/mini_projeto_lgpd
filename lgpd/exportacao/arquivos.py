"""Rotinas de arquivos para a atividade de exportação LGPD."""
import csv
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from lgpd.protecao.validacao import celula_segura


def criar_diretorio_execucao(destino):
    """Crie um diretório exclusivo para preservar exportações anteriores.

    Args:
        destino: Diretório que recebe os arquivos.

    Returns:
        Path: Diretório privado exclusivo da execução.

    Raises:
        OSError: Se não houver permissão para criar a saída.
    """
    pai = Path(destino).expanduser().resolve()
    pai.mkdir(mode=0o700, parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='lgpd-', dir=pai))


def arquivo_texto_privado(caminho, codificacao='utf-8'):
    """Abra um novo arquivo com permissões restritas em sistemas POSIX.

    Args:
        caminho: Caminho do arquivo ou diretório.
        codificacao: Codificação utilizada no texto.

    Returns:
        TextIO: Arquivo novo, pertencente ao chamador.

    Raises:
        OSError: Se o arquivo existir ou não puder ser criado.
    """
    descritor = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        return os.fdopen(descritor, 'w', encoding=codificacao, newline='')
    except (OSError, ValueError):
        os.close(descritor)
        raise


@contextmanager
def exportacoes_temporarias(diretorio_execucao):
    """Publique o lote somente após a conclusão de todas as exportações.

    Args:
        diretorio_execucao: Diretório exclusivo da execução.

    Yields:
        Path: Diretório temporário no mesmo sistema de arquivos da saída.

    Raises:
        OSError: Se a publicação ou a limpeza dos arquivos falhar.
    """
    with tempfile.TemporaryDirectory(prefix='.pendente-', dir=diretorio_execucao) as temporario:
        temporarios = Path(temporario)
        yield temporarios
        # O diretório final só aparece quando o lote está completo.
        temporarios.rename(diretorio_execucao / 'exportacoes')


def escrever_csv(caminho, cabecalhos, linhas):
    """Grave o CSV em UTF-8 sem alterar os valores aprovados pela validação.

    Args:
        caminho: Caminho do arquivo ou diretório.
        cabecalhos: Nomes das colunas, na ordem de saída.
        linhas: Registros que serão percorridos.

    Returns:
        int: Quantidade de linhas de dados gravadas, sem o cabeçalho.

    Raises:
        ValueError: Se uma célula for insegura.
        OSError: Se a gravação falhar.
    """
    caminho.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    quantidade = 0
    with arquivo_texto_privado(caminho, 'utf-8-sig') as fluxo:
        escritor = csv.writer(fluxo, quoting=csv.QUOTE_ALL)
        escritor.writerow(cabecalhos)
        for linha in linhas:
            escritor.writerow(tuple((celula_segura(valor) for valor in linha)))
            quantidade += 1
    return quantidade
