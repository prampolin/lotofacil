import random

from .statistics import DomainError, integer

CONSTRAINT_DEFAULTS = {"odd_min": 3, "odd_max": 13, "sum_min": 120, "sum_max": 270}
MAX_ATTEMPTS = 10000


def validate_seed(seed):
    if seed is not None:
        integer(seed, "seed", -(2**63), 2**63 - 1)


def validate_constraints(constraints):
    if constraints is None:
        constraints = {}
    if (
        not isinstance(constraints, dict)
        or constraints.keys() - CONSTRAINT_DEFAULTS.keys()
    ):
        raise DomainError("Restrições desconhecidas ou inválidas.")
    applied = {**CONSTRAINT_DEFAULTS, **constraints}
    for key, value in applied.items():
        integer(
            value,
            key,
            0 if key.startswith("odd") else 120,
            15 if key.startswith("odd") else 270,
        )
    if (
        applied["odd_min"] > applied["odd_max"]
        or applied["sum_min"] > applied["sum_max"]
    ):
        raise DomainError("Mínimos não podem exceder máximos.")
    # Exact reachable (odd_count, sum) pairs for a 15-number subset.
    reachable = {(0, 0, 0)}
    for n in range(1, 26):
        reachable |= {
            (size + 1, odd + n % 2, total + n)
            for size, odd, total in reachable
            if size < 15
        }
    if not any(
        size == 15
        and applied["odd_min"] <= odd <= applied["odd_max"]
        and applied["sum_min"] <= total <= applied["sum_max"]
        for size, odd, total in reachable
    ):
        raise DomainError("Restrições impossíveis para 15 dezenas.")
    return applied


def generate_games(quantity=1, seed=None, constraints=None):
    integer(quantity, "quantity", 1, 100)
    validate_seed(seed)
    applied = validate_constraints(constraints)
    rng = random.Random(seed)
    games = []
    seen = set()
    for attempts in range(1, MAX_ATTEMPTS + 1):
        game = tuple(sorted(rng.sample(range(1, 26), 15)))
        odd = sum(n % 2 for n in game)
        if (
            game in seen
            or not applied["odd_min"] <= odd <= applied["odd_max"]
            or not applied["sum_min"] <= sum(game) <= applied["sum_max"]
        ):
            continue
        seen.add(game)
        games.append(list(game))
        if len(games) == quantity:
            return {
                "games": games,
                "quantity": quantity,
                "seed": seed,
                "constraints": applied,
                "attempts": attempts,
            }
    raise DomainError(
        "Limite de 10000 tentativas atingido; relaxe as restrições ou reduza quantity."
    )
