from collections import Counter

from infra.rng import QuantumRNG
from .schemas import VoteResult

LOW_VOTES_THRESHOLD = 3  # порог предупреждения о малом числе голосов

VOTE_TTL = 3600  # Голосование живёт 5 минут

async def calculate_quantum_results(
    vote_data: dict,
    qrng: QuantumRNG,
) -> VoteResult:
    """
    Определяет победителя через взвешенную квантовую случайность.
    Вероятности пропорциональны голосам.
    """
    votes = vote_data.get("votes", {})
    options = vote_data.get("options", [])

    counter = Counter(votes.values())
    weights = [counter.get(idx, 0) for idx in range(len(options))]
    total = sum(weights)

    # Квантовый выбор (при нулевых весах — равномерно случайно)
    winner_idx = await qrng.weighted_choice(weights)

    # Вероятности в процентах
    if total > 0:
        probabilities = [round(w / total * 100, 1) for w in weights]
    else:
        uniform = round(100 / len(options), 1) if options else 0.0
        probabilities = [uniform for _ in options]
