from common.texts import COIN_SIDE


def get_flip_answer_msg(bit: int) -> str:
    result = COIN_SIDE[bit]
    return f"Результат: <b>{result}</b>"
