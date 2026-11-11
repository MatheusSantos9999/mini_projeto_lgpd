"""Verificações da execução padrão para apresentação do projeto."""
import io
import tempfile
from pathlib import Path
from unittest import TestCase, mock
from lgpd.execucao.aplicacao import principal
from lgpd.execucao.argumentos import ler_argumentos
from lgpd.execucao.menu import selecionar_opcoes

CONFERENCIA = TestCase()


def testar_opcoes_padrao():
    """Selecione as duas atividades e os dados incluídos sem argumentos."""
    opcoes = ler_argumentos([])
    CONFERENCIA.assertTrue(opcoes.demonstracao)
    CONFERENCIA.assertEqual(opcoes.atividade, 'todas')


def testar_postgres_explicito():
    """Exija a opção PostgreSQL para solicitar um banco externo."""
    CONFERENCIA.assertFalse(ler_argumentos(['--postgres']).demonstracao)
    CONFERENCIA.assertTrue(ler_argumentos(['--demonstracao']).demonstracao)
    with mock.patch('sys.stderr', new=io.StringIO()):
        with CONFERENCIA.assertRaises(SystemExit) as erro:
            ler_argumentos(['--postgres', '--demonstracao'])
    CONFERENCIA.assertEqual(erro.exception.code, 2)


def testar_exportacao_sem_conexao_externa():
    """Gere os CSVs padrão sem solicitar host, banco ou credenciais."""
    with tempfile.TemporaryDirectory() as pasta:
        with mock.patch('builtins.input', side_effect=AssertionError('Entrada inesperada')):
            with mock.patch('sys.stdout', new=io.StringIO()):
                CONFERENCIA.assertEqual(principal(['--saida', pasta]), 0)
        caminhos = {p.relative_to(p.parents[2]).as_posix() for p in Path(pasta).rglob('*.csv')}
        CONFERENCIA.assertEqual(caminhos, {'exportacoes/mascarados/1990.csv',
                                         'exportacoes/mascarados/1991.csv',
                                         'exportacoes/identificados/todos.csv'})


def testar_menu_completo():
    """Exporte as duas atividades pelas respostas do menu, sem argumentos."""
    with tempfile.TemporaryDirectory() as pasta:
        with mock.patch('builtins.input', side_effect=['', '', '', pasta]) as entrada:
            with mock.patch('sys.stdout', new=io.StringIO()):
                CONFERENCIA.assertEqual(principal([]), 0)
        CONFERENCIA.assertEqual(entrada.call_count, 4)
        CONFERENCIA.assertEqual(len(list(Path(pasta).rglob('*.csv'))), 3)


def testar_menu_postgres():
    """Configure PostgreSQL pelo menu sem precisar de argumentos de comando."""
    with mock.patch('builtins.input', side_effect=['2', '1', '1990', 'arquivos', '1']):
        with mock.patch('sys.stdout', new=io.StringIO()):
            opcoes = selecionar_opcoes([])
    CONFERENCIA.assertFalse(opcoes.demonstracao)
    CONFERENCIA.assertEqual((opcoes.atividade, opcoes.ano), ('2', 1990))
    CONFERENCIA.assertEqual(opcoes.saida, Path('arquivos'))
    CONFERENCIA.assertEqual(opcoes.modo_ssl, 'verify-full')


def testar_menu_repetir_entrada():
    """Pergunte novamente após origem, atividade ou ano inválidos."""
    respostas = ['x', '1', '9', '1', '0', 'abc', '1990', 'arquivos']
    with mock.patch('builtins.input', side_effect=respostas) as entrada:
        with mock.patch('sys.stdout', new=io.StringIO()) as saida:
            opcoes = selecionar_opcoes([])
    CONFERENCIA.assertEqual((opcoes.atividade, opcoes.ano), ('2', 1990))
    CONFERENCIA.assertEqual(entrada.call_count, len(respostas))
    CONFERENCIA.assertIn('Opção inválida', saida.getvalue())


def testar_menu_sem_filtro_identificados():
    """Não pergunte ano ou TLS na atividade 3 com os dados incluídos."""
    with mock.patch('builtins.input', side_effect=['1', '2', 'arquivos']) as entrada:
        with mock.patch('sys.stdout', new=io.StringIO()):
            opcoes = selecionar_opcoes([])
    CONFERENCIA.assertEqual(opcoes.atividade, '3')
    CONFERENCIA.assertIsNone(opcoes.ano)
    CONFERENCIA.assertEqual(entrada.call_count, 3)


def testar_menu_sair():
    """Encerre a escolha zero sem iniciar exportações."""
    with mock.patch('builtins.input', return_value='0'):
        with mock.patch('lgpd.execucao.aplicacao.executar_exportacao') as exportar:
            with mock.patch('sys.stdout', new=io.StringIO()):
                CONFERENCIA.assertEqual(principal([]), 0)
    exportar.assert_not_called()


def testar_menu_entrada_encerrada():
    """Informe a falta de entrada interativa sem apresentar rastreamento de erro."""
    with mock.patch('builtins.input', side_effect=EOFError):
        with mock.patch('sys.stdout', new=io.StringIO()), mock.patch('sys.stderr', new=io.StringIO()) as saida:
            CONFERENCIA.assertEqual(principal([]), 1)
    CONFERENCIA.assertIn('terminal integrado', saida.getvalue())


CENARIOS = (testar_opcoes_padrao, testar_postgres_explicito,
            testar_exportacao_sem_conexao_externa, testar_menu_completo,
            testar_menu_postgres, testar_menu_repetir_entrada,
            testar_menu_sem_filtro_identificados, testar_menu_sair,
            testar_menu_entrada_encerrada)
