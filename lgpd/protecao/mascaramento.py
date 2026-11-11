"""Rotinas de mascaramento para a atividade de exportação LGPD."""
from lgpd.protecao.validacao import conferir_texto, texto_obrigatorio
PADRAO_CPF = '(?:[0-9]{11}|[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2})'


def mascarar_nome(valor):
    """Preserve a inicial do primeiro nome e o restante do sobrenome.

    Args:
        valor: Valor recebido para validação.

    Returns:
        str: Inicial do primeiro nome, asteriscos e sobrenomes preservados.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    nome = texto_obrigatorio(valor, 'nome')
    inicial, restante, sobrenome = conferir_texto('(\\S)(\\S*)(.*)', nome, 'nome').groups()
    return inicial + '*' * len(restante) + sobrenome


def mascarar_cpf(valor):
    """Preserve apenas os três primeiros dígitos, sem validar os verificadores.

    Args:
        valor: Valor recebido para validação.

    Returns:
        str: CPF no formato 000.***.***-**, preservando os três primeiros dígitos.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    cpf = conferir_texto(PADRAO_CPF, valor, 'CPF').group()
    return cpf[:3] + '.***.***-**'


def mascarar_email(valor):
    """Preserve a inicial do endereço e o domínio completo.

    Args:
        valor: Valor recebido para validação.

    Returns:
        str: Inicial, asteriscos e domínio completo do endereço.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    padrao = '([^@\\s])([^@\\s]*)@([^@\\s]+\\.[^@\\s]+)'
    inicial, restante, dominio = conferir_texto(padrao, valor, 'email').groups()
    return inicial + '*' * len(restante) + '@' + dominio


def mascarar_telefone(valor):
    """Preserve somente os quatro últimos dígitos do telefone.

    Args:
        valor: Valor recebido para validação.

    Returns:
        str: Os quatro últimos dígitos, sem pontuação.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    telefone = conferir_texto('\\+?[0-9 ()-]+', valor, 'telefone').group()
    digitos = telefone.translate(str.maketrans('', '', '+ ()-'))
    return conferir_texto('[0-9]{4,15}', digitos, 'telefone').group()[-4:]


def mascarar_registro(linha):
    """Aplique as quatro máscaras e preserve o identificador e as datas.

    Args:
        linha: Valor utilizado nesta operação.

    Returns:
        tuple: Oito campos, com as máscaras em nome, CPF, e-mail e telefone.

    Raises:
        ValueError: Se os dados ou parâmetros forem inválidos.
    """
    try:
        identificador, nome, cpf, email, telefone, nascimento, criado, atualizado = linha
    except (TypeError, ValueError):
        raise ValueError('O registro deve conter exatamente oito campos.') from None
    return (identificador, mascarar_nome(nome), mascarar_cpf(cpf), mascarar_email(email), mascarar_telefone(telefone), nascimento, criado, atualizado)
