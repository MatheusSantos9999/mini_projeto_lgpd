"""Leitura e validação das respostas do menu no terminal."""
from functools import partial
from itertools import count
from lgpd.protecao.validacao import validar_ano


def ler_valor(pergunta, converter, padrao=''):
    """Repita a pergunta até receber um valor aceito pelo conversor.

    Args:
        pergunta (str): Pergunta exibida no terminal.
        converter (Callable): Operação que valida e converte a resposta.
        padrao (str): Resposta utilizada quando o operador pressiona Enter.

    Returns:
        object: Resposta validada e convertida.

    Raises:
        EOFError: Se o terminal não disponibilizar entrada.
        KeyboardInterrupt: Se o operador cancelar a execução.
    """
    for _ in count():
        try:
            return converter(input(pergunta).strip() or padrao)
        except ValueError as erro:
            print(erro)


def converter_escolha(resposta, opcoes):
    """Converta a opção digitada sem aceitar valores fora do menu.

    Args:
        resposta (str): Número escolhido pelo operador.
        opcoes (dict): Correspondência entre números e valores da aplicação.

    Returns:
        object: Valor associado à opção escolhida.

    Raises:
        ValueError: Se a resposta não corresponder a uma opção.
    """
    try:
        return opcoes[resposta]
    except KeyError:
        raise ValueError('Opção inválida. Digite um dos números apresentados.') from None


def ler_escolha(pergunta, opcoes, padrao='1'):
    """Leia uma opção de menu com nova tentativa para respostas inválidas.

    Args:
        pergunta (str): Menu e pergunta exibidos no terminal.
        opcoes (dict): Valores permitidos para a resposta.
        padrao (str): Opção utilizada ao pressionar Enter.

    Returns:
        object: Valor correspondente à opção válida.
    """
    return ler_valor(pergunta, partial(converter_escolha, opcoes=opcoes), padrao)


def ano_opcional(resposta):
    """Aceite um ano válido ou deixe a exportação sem filtro.

    Args:
        resposta (str): Ano digitado; texto vazio representa todos os anos.

    Returns:
        int | None: Ano validado ou ausência de filtro.

    Raises:
        ValueError: Se o ano estiver fora do calendário aceito.
    """
    if not resposta:
        return None
    return validar_ano(resposta)
