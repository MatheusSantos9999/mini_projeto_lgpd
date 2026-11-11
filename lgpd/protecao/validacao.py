"""Rotinas de validacao para a atividade de exportação LGPD."""
import re
import unicodedata
from datetime import date


def conferir_texto(padrao, valor, campo):
    """Confira todo o texto com o padrão sem expor o valor recusado.

    Args:
        padrao: Expressão regular esperada.
        valor: Valor recebido para validação.
        campo: Nome público do campo para a mensagem de erro.

    Returns:
        re.Match: Correspondência completa com o padrão informado.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    try:
        resultado = re.fullmatch(padrao, valor)
        resultado.group()
        return resultado
    except (TypeError, AttributeError):
        raise ValueError(f'Formato inválido para {campo}.') from None


def texto_obrigatorio(valor, campo):
    """Exija um texto não vazio, sem quebras de linha ou controles.

    Args:
        valor: Valor recebido para validação.
        campo: Nome público do campo para a mensagem de erro.

    Returns:
        str: Texto original validado, sem alterações.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    return conferir_texto('(?=\\S)[^\\x00-\\x1f\\x7f]+', valor, campo).group()


def validar_ano(valor):
    """Converta o ano para um inteiro entre um e 9.999.

    Args:
        valor: Valor recebido para validação.

    Returns:
        int: Ano entre 1 e 9999.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    try:
        return date(int(conferir_texto('[0-9]{1,4}', str(valor), 'ano').group()), 1, 1).year
    except (ValueError, TypeError, OverflowError):
        raise ValueError('O ano deve ser inteiro entre 1 e 9999.') from None


def celula_segura(valor):
    """Recuse textos que podem ser interpretados como fórmulas ou controles.

    Args:
        valor: Valor recebido para validação.

    Returns:
        object: Valor original adequado à gravação no CSV.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    try:
        valor.encode('utf-8')
    except AttributeError:
        return valor
    except UnicodeError:
        raise ValueError('Codificação de texto inválida.') from None
    conferir_controles(valor)
    padrao = '(?!\\s*[=+@\\-＝＋＠－])[^\\x00-\\x1f\\x7f]*'
    return conferir_texto(padrao, valor, 'célula da planilha').group()


def conferir_controles(texto):
    """Recuse controles e caracteres invisíveis que escondem fórmulas de planilha.

    Args:
        texto (str): Texto destinado ao CSV.

    Raises:
        ValueError: Se houver caracteres de controle ou formatação invisível.
    """
    try:
        (False,).index(any(unicodedata.category(c).startswith('C') for c in texto))
    except ValueError:
        raise ValueError('A célula contém caracteres de controle ou formatação.') from None


def validar_porta(valor):
    """Valide o número da porta antes de tentar abrir a conexão.

    Args:
        valor (str | int): Número da porta fornecido pelo operador.

    Returns:
        int: Porta entre 1 e 65535.

    Raises:
        ValueError: Se o valor não representar uma porta válida.
    """
    porta = int(conferir_texto(r'[0-9]{1,5}', str(valor), 'porta').group())
    try:
        (True,).index(1 <= porta <= 65535)
    except ValueError:
        raise ValueError('A porta deve ser um inteiro entre 1 e 65535.') from None
    return porta
