"""Verificações das correções de validação, logs e organização."""
import ast
import io
import logging
from pathlib import Path
from unittest import TestCase, mock
from lgpd.monitoramento.registros import criar_registrador
from lgpd.monitoramento.tempo import medir_tempo
from lgpd.protecao.validacao import celula_segura, validar_porta
from testes.casos import falha_cronometrada, sucesso_cronometrado

CONFERENCIA = TestCase()


def testar_porta_validada():
    """Recuse portas inválidas antes de tentar qualquer conexão."""
    for valor in (0, -1, 65536, True, '5432 OR 1=1', 54.32):
        with CONFERENCIA.assertRaises(ValueError):
            validar_porta(valor)
    CONFERENCIA.assertEqual(validar_porta('5432'), 5432)
    CONFERENCIA.assertEqual(validar_porta(65535), 65535)


def testar_controles_invisiveis():
    """Recuse textos invisíveis que podem esconder uma fórmula."""
    for valor in ('\ufeff=1', '\u200b=1', 'nome\u202eoculto', '\x85=1'):
        with CONFERENCIA.assertRaises(ValueError):
            celula_segura(valor)
    CONFERENCIA.assertEqual(celula_segura('Érica Souza'), 'Érica Souza')


def testar_registradores_sem_acumulo():
    """Evite acumular registradores globais a cada nova exportação."""
    quantidade = len(logging.Logger.manager.loggerDict)
    for _ in range(20):
        registrador, manipulador = criar_registrador(io.StringIO())
        registrador.removeHandler(manipulador)
        manipulador.close()
    CONFERENCIA.assertEqual(len(logging.Logger.manager.loggerDict), quantidade)


def testar_decorador_sem_registrador():
    """Informe o argumento ausente sem esconder a falha com um KeyError."""
    with CONFERENCIA.assertRaisesRegex(TypeError, 'registrador'):
        medir_tempo(sucesso_cronometrado)()


def testar_falha_do_log_preserva_erro():
    """Preserve a exceção da operação quando o registrador também falha."""
    registrador = mock.Mock()
    registrador.info.side_effect = OSError('caminho privado')
    with mock.patch('sys.stderr', new=io.StringIO()) as saida:
        with CONFERENCIA.assertRaisesRegex(ValueError, 'valor-privado'):
            medir_tempo(falha_cronometrada)(registrador=registrador)
    CONFERENCIA.assertNotIn('caminho privado', saida.getvalue())


def linhas_executaveis(funcao, linhas):
    """Conte o corpo físico sem documentação, comentários ou linhas vazias.

    Args:
        funcao (ast.FunctionDef): Função a conferir.
        linhas (list[str]): Código-fonte do módulo.

    Returns:
        int: Quantidade de linhas do corpo executável.
    """
    inicio = funcao.body[1].lineno if ast.get_docstring(funcao) else funcao.body[0].lineno
    return sum(bool(l.strip()) and not l.lstrip().startswith('#')
               for l in linhas[inicio - 1:funcao.end_lineno])


def conferir_modulo(caminho):
    """Confira a documentação e o limite de linhas das funções do módulo.

    Args:
        caminho (Path): Módulo Python do projeto.
    """
    texto = caminho.read_text(encoding='utf-8')
    for funcao in ast.walk(ast.parse(texto)):
        if isinstance(funcao, (ast.FunctionDef, ast.AsyncFunctionDef)):
            CONFERENCIA.assertTrue(ast.get_docstring(funcao), (caminho, funcao.name))
            CONFERENCIA.assertLessEqual(linhas_executaveis(funcao, texto.splitlines()), 10,
                                       (caminho.name, funcao.name))


def testar_limite_de_linhas():
    """Mantenha todas as funções documentadas e com até dez linhas executáveis."""
    raiz = Path(__file__).resolve().parents[1]
    for pasta in ('lgpd', 'inicializacao', 'testes'):
        for caminho in (raiz / pasta).rglob('*.py'):
            conferir_modulo(caminho)
    conferir_modulo(raiz / 'main.py')


CENARIOS = (testar_porta_validada, testar_controles_invisiveis,
            testar_registradores_sem_acumulo, testar_decorador_sem_registrador,
            testar_falha_do_log_preserva_erro, testar_limite_de_linhas)
