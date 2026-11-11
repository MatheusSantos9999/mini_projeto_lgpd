"""Rotinas de tempo para a atividade de exportação LGPD."""
from functools import partial, wraps
from time import perf_counter
import sys


def medir_tempo(funcao):
    """Decore uma exportação preservando seu resultado e sua documentação.

    Args:
        funcao: Operação que será chamada.

    Returns:
        Callable: Operação decorada com os metadados originais.
    """
    return wraps(funcao)(partial(invocar_cronometrado, funcao))


def invocar_cronometrado(funcao, *argumentos, **opcoes):
    """Execute a operação e registre a duração tanto no sucesso quanto na falha.

    Args:
        funcao: Operação que será chamada.
        *argumentos: Argumentos posicionais encaminhados sem registro.
        **opcoes: Argumentos nomeados encaminhados sem registro.

    Returns:
        object: Mesmo resultado da operação recebida.

    Raises:
        TypeError: Se não houver registrador. Erros da operação são propagados.
    """
    registrador = obter_registrador(opcoes)
    inicio, situacao = (perf_counter(), 'falha')
    try:
        resultado = funcao(*argumentos, **opcoes)
        situacao = 'sucesso'
        return resultado
    finally:
        registrar_tempo(registrador, funcao.__name__, inicio, situacao)


def registrar_tempo(registrador, operacao, inicio, situacao):
    """Registre somente operação, resultado e duração, sem os dados exportados.

    Args:
        registrador: Registrador de eventos desta execução.
        operacao: Nome da operação, sem conteúdo dos registros.
        inicio: Instante inicial do relógio monotônico.
        situacao: Resultado registrado para a operação.

    Returns:
        None: O evento é encaminhado ao registrador.
    """
    try:
        registrador.info('operacao=%s situacao=%s segundos=%.6f', operacao, situacao, perf_counter() - inicio)
    except Exception:
        print('Não foi possível registrar a duração da operação.', file=sys.stderr)


def obter_registrador(opcoes):
    """Exija o registrador antes de executar a operação decorada.

    Args:
        opcoes (dict): Argumentos nomeados da chamada.

    Returns:
        logging.Logger: Registrador fornecido pela execução.

    Raises:
        TypeError: Se o argumento obrigatório estiver ausente.
    """
    try:
        registrador = opcoes['registrador']
        (True,).index(callable(registrador.info))
        return registrador
    except (KeyError, AttributeError, ValueError):
        raise TypeError('Informe o registrador como argumento nomeado.') from None
