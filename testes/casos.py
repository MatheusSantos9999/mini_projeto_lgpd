"""Rotinas de casos para a atividade de exportação LGPD."""
import csv
import io
import logging
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from unittest import TestCase, mock, skipUnless
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from lgpd.monitoramento.tempo import medir_tempo
from lgpd.exportacao.atividades import exportar_por_ano, exportar_identificados, executar_atividades
from lgpd.execucao.argumentos import ler_argumentos
from lgpd.dados.banco import abrir_postgres
from lgpd.dados.demonstracao import registro_demonstracao, abrir_demonstracao
from lgpd.exportacao.arquivos import arquivo_texto_privado, exportacoes_temporarias, escrever_csv
from lgpd.monitoramento.registros import criar_registrador
from lgpd.protecao.mascaramento import mascarar_cpf, mascarar_email, mascarar_nome, mascarar_telefone, mascarar_registro
from lgpd.dados.repositorio import anos_nascimento, registros_por_ano
from lgpd.dados.esquema import USUARIOS
from lgpd.protecao.validacao import celula_segura, validar_ano
from lgpd.execucao.aplicacao import executar_exportacao, principal
CONFERENCIA = TestCase()
REGISTRADOR = logging.getLogger('lgpd.tests.null')
REGISTRADOR.addHandler(logging.NullHandler())
REGISTRADOR.propagate = False


def conferir_valor(funcao, valor, esperado):
    """Compare a transformação com o resultado esperado.

    Args:
        funcao: Operação que será chamada.
        valor: Valor recebido para validação.
        esperado: Resultado esperado pelo teste.
    """
    CONFERENCIA.assertEqual(funcao(valor), esperado)


def conferir_invalido(funcao, valor):
    """Confira se uma entrada inválida é recusada.

    Args:
        funcao: Operação que será chamada.
        valor: Valor recebido para validação.
    """
    with CONFERENCIA.assertRaises(ValueError):
        funcao(valor)


def ler_csv(caminho):
    """Leia o CSV gerado para conferir seu cabeçalho e seus registros.

    Args:
        caminho: Caminho do arquivo ou diretório.

    Returns:
        list[list[str]]: Linhas do arquivo, incluindo o cabeçalho.
    """
    with caminho.open(encoding='utf-8-sig', newline='') as fluxo:
        return list(csv.reader(fluxo))


def testar_registro_atividade():
    """Verifique registro atividade."""
    nascimento, marca = (date(1990, 8, 24), datetime(2025, 10, 9, 20, 40, 40))
    origem = (1, 'Olivia Araújo', '237.615.809-59', 'nuneserick@example.com', '+55 (011) 9483-6810', nascimento, marca, marca)
    esperado = (1, 'O***** Araújo', '237.***.***-**', 'n*********@example.com', '6810', nascimento, marca, marca)
    CONFERENCIA.assertEqual(mascarar_registro(origem), esperado)
    CONFERENCIA.assertEqual(origem[1], 'Olivia Araújo')


def testar_exportacao_anos():
    """Verifique exportacao anos."""
    with tempfile.TemporaryDirectory() as pasta, abrir_demonstracao() as conexao:
        destino = Path(pasta)
        CONFERENCIA.assertEqual(exportar_por_ano(conexao, destino, registrador=REGISTRADOR), 3)
        primeiro, segundo = (ler_csv(destino / 'mascarados/1990.csv'), ler_csv(destino / 'mascarados/1991.csv'))
        CONFERENCIA.assertEqual((len(primeiro), len(segundo)), (2, 3))
        CONFERENCIA.assertTrue(all((linha[5].startswith('1990-') for linha in primeiro[1:])))
        CONFERENCIA.assertTrue(all((linha[5].startswith('1991-') for linha in segundo[1:])))
        CONFERENCIA.assertEqual(primeiro[1][1:5], ['P***** Amostra', '000.***.***-**', 'p******@example.invalid', '0000'])


def testar_ano_selecionado():
    """Verifique ano selecionado."""
    with tempfile.TemporaryDirectory() as pasta, abrir_demonstracao() as conexao:
        destino = Path(pasta)
        CONFERENCIA.assertEqual(exportar_por_ano(conexao, destino, 1990, registrador=REGISTRADOR), 1)
        CONFERENCIA.assertEqual([p.name for p in (destino / 'mascarados').iterdir()], ['1990.csv'])


def testar_ano_ausente():
    """Verifique ano ausente."""
    with tempfile.TemporaryDirectory() as pasta, abrir_demonstracao() as conexao:
        destino = Path(pasta)
        CONFERENCIA.assertEqual(exportar_por_ano(conexao, destino, 2000, registrador=REGISTRADOR), 0)
        CONFERENCIA.assertEqual(len(ler_csv(destino / 'mascarados/2000.csv')), 1)


def testar_exportacao_identificada():
    """Verifique exportacao identificada."""
    with tempfile.TemporaryDirectory() as pasta, abrir_demonstracao() as conexao:
        destino = Path(pasta)
        CONFERENCIA.assertEqual(exportar_identificados(conexao, destino, 1990, registrador=REGISTRADOR), 3)
        linhas = ler_csv(destino / 'identificados/todos.csv')
        CONFERENCIA.assertEqual(linhas[0], ['nome', 'cpf'])
        CONFERENCIA.assertEqual(linhas[1], ['Pessoa Exemplo', '000.000.000-00'])
        CONFERENCIA.assertTrue(all((len(linha) == 2 for linha in linhas)))


def testar_banco_vazio():
    """Verifique banco vazio."""
    with tempfile.TemporaryDirectory() as pasta, abrir_demonstracao() as conexao:
        conexao.execute(USUARIOS.delete())
        CONFERENCIA.assertEqual(anos_nascimento(conexao), ())
        CONFERENCIA.assertEqual(exportar_por_ano(conexao, Path(pasta), registrador=REGISTRADOR), 0)
        CONFERENCIA.assertEqual(exportar_identificados(conexao, Path(pasta), registrador=REGISTRADOR), 0)
        CONFERENCIA.assertEqual(ler_csv(Path(pasta) / 'identificados/todos.csv'), [['nome', 'cpf']])


def testar_mais_de_dez_registros():
    """Verifique mais de dez registros."""
    with tempfile.TemporaryDirectory() as pasta, abrir_demonstracao() as conexao:
        conexao.execute(USUARIOS.insert(), [registro_demonstracao(i, 'Pessoa Fictícia', 1990) for i in range(4, 31)])
        CONFERENCIA.assertEqual(exportar_identificados(conexao, Path(pasta), registrador=REGISTRADOR), 30)
        CONFERENCIA.assertEqual(len(ler_csv(Path(pasta) / 'identificados/todos.csv')), 31)


def linhas_com_falha():
    """Produza um registro e interrompa o fluxo para testar a limpeza.

    Yields:
        tuple: Um registro fictício antes da interrupção planejada.

    Raises:
        OSError: Interrupção proposital do fluxo de dados.
    """
    yield ('Pessoa Fictícia', '000.000.000-00')
    raise OSError('Interrupção de teste.')


def testar_limpeza_lote():
    """Verifique limpeza lote."""
    with tempfile.TemporaryDirectory() as pasta:
        diretorio = Path(pasta)
        with CONFERENCIA.assertRaises(OSError):
            with exportacoes_temporarias(diretorio) as temporarios:
                escrever_csv(temporarios / 'todos.csv', ('nome', 'cpf'), linhas_com_falha())
        CONFERENCIA.assertEqual(list(diretorio.iterdir()), [])


def testar_publicacao_atomica():
    """Verifique publicacao atomica."""
    with tempfile.TemporaryDirectory() as pasta:
        diretorio = Path(pasta)
        with exportacoes_temporarias(diretorio) as temporarios:
            escrever_csv(temporarios / 'todos.csv', ('nome', 'cpf'), [('Pessoa Teste', '000.000.000-00')])
            CONFERENCIA.assertFalse((diretorio / 'exportacoes').exists())
        CONFERENCIA.assertEqual(ler_csv(diretorio / 'exportacoes/todos.csv')[1][0], 'Pessoa Teste')


def testar_nao_sobrescrever():
    """Verifique nao sobrescrever."""
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / 'existing.csv'
        caminho.write_text('preservar', encoding='utf-8')
        with CONFERENCIA.assertRaises(FileExistsError):
            arquivo_texto_privado(caminho)
        CONFERENCIA.assertEqual(caminho.read_text(), 'preservar')


@skipUnless(os.name == 'posix', 'Permissões POSIX exigem uma plataforma POSIX.')
def testar_permissao_privada():
    """Verifique permissao privada."""
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / 'private.csv'
        with arquivo_texto_privado(caminho) as fluxo:
            fluxo.write('teste')
        CONFERENCIA.assertEqual(caminho.stat().st_mode & 511, 384)


def sucesso_cronometrado(*, registrador):
    """Retorne um resultado fixo para conferir o decorador.

    Args:
        registrador: Registrador de eventos desta execução.

    Returns:
        int: Valor fixo usado na conferência do decorador.
    """
    return 42


def falha_cronometrada(*, registrador):
    """Provoque uma falha sem permitir que a mensagem entre no log.

    Args:
        registrador: Registrador de eventos desta execução.

    Raises:
        ValueError: Falha proposital para verificar a preservação do erro.
    """
    raise ValueError('valor-privado-nao-deve-ir-ao-log')


def testar_tempo_sucesso():
    """Verifique tempo sucesso."""
    fluxo = io.StringIO()
    registrador, seletor = criar_registrador(fluxo)
    decorada = medir_tempo(sucesso_cronometrado)
    CONFERENCIA.assertEqual(decorada(registrador=registrador), 42)
    CONFERENCIA.assertEqual(decorada.__name__, 'sucesso_cronometrado')
    CONFERENCIA.assertIn('situacao=sucesso segundos=', fluxo.getvalue())
    registrador.removeHandler(seletor)
    seletor.close()


def testar_tempo_falha():
    """Verifique tempo falha."""
    fluxo = io.StringIO()
    registrador, seletor = criar_registrador(fluxo)
    with CONFERENCIA.assertRaises(ValueError):
        medir_tempo(falha_cronometrada)(registrador=registrador)
    CONFERENCIA.assertIn('situacao=falha segundos=', fluxo.getvalue())
    CONFERENCIA.assertNotIn('valor-privado', fluxo.getvalue())
    registrador.removeHandler(seletor)
    seletor.close()


def testar_execucao_completa():
    """Verifique execucao completa."""
    with tempfile.TemporaryDirectory() as pasta:
        opcoes = ler_argumentos(['--demonstracao', '--atividade', 'todas', '--saida', pasta])
        diretorio, contagens = executar_exportacao(opcoes)
        CONFERENCIA.assertEqual(contagens, {'exportar_por_ano': 3, 'exportar_identificados': 3})
        CONFERENCIA.assertTrue((diretorio / 'exportacoes/identificados/todos.csv').exists())
        registro = (diretorio / 'execucao.log').read_text()
        CONFERENCIA.assertEqual(registro.count('situacao=sucesso'), 2)
        CONFERENCIA.assertNotIn('Pessoa', registro)


def testar_banco_preservado():
    """Verifique banco preservado."""
    with tempfile.TemporaryDirectory() as pasta, abrir_demonstracao() as conexao:
        anterior = list(conexao.execute(select(USUARIOS)))
        executar_atividades(conexao, Path(pasta), 'todas', None, REGISTRADOR)
        CONFERENCIA.assertEqual(list(conexao.execute(select(USUARIOS))), anterior)


def testar_postgres_somente_leitura():
    """Verifique postgres somente leitura."""
    motor = mock.MagicMock()
    conexao = motor.connect.return_value.__enter__.return_value
    with mock.patch('lgpd.dados.banco.criar_conexao_postgres', return_value=motor):
        with abrir_postgres(object()) as real:
            CONFERENCIA.assertIs(real, conexao)
    conexao.exec_driver_sql.assert_any_call('SET TRANSACTION READ ONLY')
    conexao.exec_driver_sql.assert_any_call("SET LOCAL statement_timeout = '60s'")
    motor.dispose.assert_called_once()


def testar_parametro_ano():
    """Verifique parametro ano."""
    from sqlalchemy import extract
    consulta = select(USUARIOS).where(extract('year', USUARIOS.c.data_nascimento) == 1990)
    compilado = consulta.compile(dialect=postgresql.dialect())
    CONFERENCIA.assertNotIn('1990', str(compilado))
    CONFERENCIA.assertIn(1990, compilado.params.values())


def testar_ano_injetado():
    """Verifique ano injetado."""
    with abrir_demonstracao() as conexao:
        with CONFERENCIA.assertRaises(ValueError):
            list(registros_por_ano(conexao, '1990 OR 1=1'))


def testar_atividade_invalida():
    """Verifique atividade invalida."""
    with CONFERENCIA.assertRaises(ValueError):
        executar_atividades(None, None, 'invalid', None, REGISTRADOR)


def testar_argumento_ano_invalido():
    """Verifique argumento ano invalido."""
    with mock.patch('sys.stderr', new=io.StringIO()):
        with CONFERENCIA.assertRaises(SystemExit) as resultado:
            ler_argumentos(['--ano', 'not-a-year'])
    CONFERENCIA.assertEqual(resultado.exception.code, 2)


def testar_falha_controlada():
    """Verifique falha controlada."""
    with mock.patch('lgpd.execucao.aplicacao.executar_exportacao', side_effect=OSError('caminho-privado')):
        with mock.patch('sys.stderr', new=io.StringIO()) as erros:
            with mock.patch('sys.stdout', new=io.StringIO()):
                CONFERENCIA.assertEqual(principal(['--demonstracao']), 1)
    CONFERENCIA.assertNotIn('caminho-privado', erros.getvalue())
CASOS_VALIDOS = ((mascarar_nome, 'Olivia Araújo', 'O***** Araújo'), (mascarar_nome, 'Ana', 'A**'), (mascarar_nome, 'Érica Souza', 'É**** Souza'), (mascarar_nome, 'A', 'A'), (mascarar_nome, 'Maria  da Silva', 'M****  da Silva'), (mascarar_cpf, '237.615.809-59', '237.***.***-**'), (mascarar_cpf, '23761580959', '237.***.***-**'), (mascarar_email, 'nuneserick@example.com', 'n*********@example.com'), (mascarar_email, 'a@example.com', 'a@example.com'), (mascarar_telefone, '+55 (011) 9483-6810', '6810'), (mascarar_telefone, '0000', '0000'), (validar_ano, '1990', 1990), (validar_ano, 9999, 9999), (celula_segura, 'Doe, Jane', 'Doe, Jane'), (celula_segura, 0, 0), (celula_segura, None, None))
CASOS_INVALIDOS = ((mascarar_nome, None), (mascarar_nome, ''), (mascarar_nome, '\nPerson'), (mascarar_cpf, '123'), (mascarar_cpf, 'abc.def.ghi-jk'), (mascarar_cpf, None), (mascarar_email, 'missing-at'), (mascarar_email, 'a@b@c.com'), (mascarar_email, None), (mascarar_telefone, '123'), (mascarar_telefone, 'call 123456789'), (mascarar_telefone, None), (mascarar_registro, (1, 2)), (mascarar_registro, None), (validar_ano, '0'), (validar_ano, '10000'), (validar_ano, True), (validar_ano, 1990.5), (validar_ano, '1990 OR 1=1'), (celula_segura, '=HYPERLINK("example")'), (celula_segura, '  +SUM(1,2)'), (celula_segura, '@SUM(1,2)'), (celula_segura, '\t=1'), (celula_segura, '－1'), (celula_segura, 'line\nbreak'), (celula_segura, '\ud800'))
CENARIOS = (testar_registro_atividade, testar_exportacao_anos, testar_ano_selecionado, testar_ano_ausente, testar_exportacao_identificada, testar_banco_vazio, testar_mais_de_dez_registros, testar_limpeza_lote, testar_publicacao_atomica, testar_nao_sobrescrever, testar_permissao_privada, testar_tempo_sucesso, testar_tempo_falha, testar_execucao_completa, testar_banco_preservado, testar_postgres_somente_leitura, testar_parametro_ano, testar_ano_injetado, testar_atividade_invalida, testar_argumento_ano_invalido, testar_falha_controlada)
