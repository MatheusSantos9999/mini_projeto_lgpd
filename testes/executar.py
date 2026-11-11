"""Rotinas de executar para a atividade de exportação LGPD."""
from functools import partial, update_wrapper
from unittest import FunctionTestCase, TestSuite, TextTestRunner
from testes.ambiente import testar_ambiente_real
from testes.execucao import CENARIOS as EXECUCAO
from testes.regressoes import CENARIOS as REGRESSOES
from testes.casos import CASOS_INVALIDOS, CENARIOS, CASOS_VALIDOS, conferir_invalido, conferir_valor


def montar_suite():
    """Reúna os cenários completos e os casos de transformação e validação.

    Returns:
        unittest.TestSuite: Conjunto dos casos e cenários do projeto.
    """
    suite = TestSuite((FunctionTestCase(funcao) for funcao in CENARIOS + REGRESSOES + EXECUCAO + (testar_ambiente_real,)))
    suite.addTests((FunctionTestCase(caso_nomeado(conferir_valor, *case), description=f'Transformação válida {indice}') for indice, case in enumerate(CASOS_VALIDOS, 1)))
    suite.addTests((FunctionTestCase(caso_nomeado(conferir_invalido, *case), description=f'Entrada recusada {indice}') for indice, case in enumerate(CASOS_INVALIDOS, 1)))
    return suite


def caso_nomeado(funcao, *argumentos):
    """Associe os argumentos ao caso e preserve os metadados para o unittest.

    Args:
        funcao: Operação que será chamada.
        *argumentos: Argumentos posicionais encaminhados sem registro.

    Returns:
        Callable: Caso de teste com os argumentos vinculados.
    """
    return update_wrapper(partial(funcao, *argumentos), funcao)


def principal():
    """Execute o programa e apresente falhas sem expor credenciais ou dados.

    Returns:
        int: Zero no sucesso ou código diferente de zero na falha.
    """
    resultado = TextTestRunner(verbosity=2).run(montar_suite())
    return int(not resultado.wasSuccessful())
if __name__ == '__main__':
    raise SystemExit(principal())
