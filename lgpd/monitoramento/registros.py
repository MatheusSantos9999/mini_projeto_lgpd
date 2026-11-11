"""Rotinas de registros para a atividade de exportação LGPD."""
import logging
from contextlib import contextmanager
from uuid import uuid4
from lgpd.exportacao.arquivos import arquivo_texto_privado


def criar_registrador(fluxo):
    """Prepare um registrador exclusivo e o manipulador de seu arquivo.

    Args:
        fluxo: Arquivo ou fluxo de texto já aberto.

    Returns:
        tuple: Registrador isolado e seu manipulador de saída.
    """
    registrador = logging.Logger('lgpd.' + uuid4().hex)
    registrador.setLevel(logging.INFO)
    registrador.propagate = False
    seletor = logging.StreamHandler(fluxo)
    seletor.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    registrador.addHandler(seletor)
    return (registrador, seletor)


@contextmanager
def registro_execucao(caminho):
    """Mantenha o arquivo de log aberto e libere os recursos no encerramento.

    Args:
        caminho: Caminho do arquivo ou diretório.

    Yields:
        logging.Logger: Registrador disponível enquanto o arquivo permanece aberto.
    """
    with arquivo_texto_privado(caminho) as fluxo:
        registrador, seletor = criar_registrador(fluxo)
        try:
            yield registrador
        finally:
            registrador.removeHandler(seletor)
            seletor.close()
