from collections import Counter

from infra.rng import QuantumRNG

VOTE_TTL = 86400  # Голосование живёт 24 часа
MAX_OPTIONS = 5


async def calculate_vote_results(vote_data: dict, qrng: QuantumRNG) -> tuple[list[int], bool]:
    """
    Подсчитывает голоса. При ничьей использует квантовый RNG для выбора победителя.
    Возвращает: (список индексов победителей, был_ли_тайбрейкер)
    """
    votes = vote_data.get("votes", {})

    if not votes:
        return [], False

    counter = Counter(votes.values())
    max_count = max(counter.values())
    winners = [idx for idx, count in counter.items() if count == max_count]

    if len(winners) == 1:
        return winners, False

    # Ничья! Используем квантовый тайбрейкер
    bits_needed = (len(winners) - 1).bit_length()
    bit_str = "".join(str(await qrng.get_bit()) for _ in range(bits_needed))
    chosen = int(bit_str, 2) % len(winners)

    return [winners[chosen]], True
