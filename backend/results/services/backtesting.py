import random

from .game_generator import validate_seed
from .statistics import DomainError, EmptyDataError, integer, ticket


def baseline_games(quantity, rng):
    games = []
    seen = set()
    # Collision is unlikely, but still bound the work explicitly.
    for _ in range(10000):
        game = tuple(sorted(rng.sample(range(1, 26), 15)))
        if game not in seen:
            seen.add(game)
            games.append(list(game))
        if len(games) == quantity:
            return games
    raise DomainError("Limite de tentativas do baseline atingido.")


def validate_config(start_contest, end_contest, mode, games, quantity, seed):
    integer(start_contest, "start_contest", 1, 2147483647)
    integer(end_contest, "end_contest", 1, 2147483647)
    if start_contest > end_contest:
        raise DomainError("Intervalo inválido.")
    if mode not in ("fixed_games", "rolling_baseline"):
        raise DomainError("mode deve ser fixed_games ou rolling_baseline.")
    validate_seed(seed)
    if mode == "fixed_games":
        if not isinstance(games, list) or not 1 <= len(games) <= 100:
            raise DomainError("fixed_games requer de 1 a 100 jogos.")
        if quantity is not None:
            raise DomainError("quantity não se aplica a fixed_games.")
        games = [ticket(game) for game in games]
        if len({tuple(game) for game in games}) != len(games):
            raise DomainError("Jogos duplicados.")
        quantity = len(games)
    else:
        if games is not None:
            raise DomainError("games não se aplica a rolling_baseline.")
        quantity = 1 if quantity is None else quantity
        integer(quantity, "quantity", 1, 100)
    return games, quantity


def evaluate(
    contests, start_contest, end_contest, mode, games=None, quantity=None, seed=None
):
    games, quantity = validate_config(
        start_contest, end_contest, mode, games, quantity, seed
    )
    rows = sorted(
        (row for row in contests if start_contest <= row.number <= end_contest),
        key=lambda row: row.number,
    )
    if not rows:
        raise EmptyDataError("Nenhum concurso encontrado.")
    if len(rows) > 200:
        raise DomainError("Avalie no máximo 200 concursos armazenados.")
    rng = random.Random(seed)
    distribution = {n: 0 for n in range(16)}
    baseline_distribution = {n: 0 for n in range(16)}
    breakdown = []
    for row in rows:
        # Generate before reading target numbers; baseline has no history input.
        baseline = baseline_games(quantity, rng)
        selected = games if mode == "fixed_games" else baseline
        drawn = set(ticket(row.numbers))
        hits = [len(set(game) & drawn) for game in selected]
        baseline_hits = [len(set(game) & drawn) for game in baseline]
        for hit in hits:
            distribution[hit] += 1
        for hit in baseline_hits:
            baseline_distribution[hit] += 1
        breakdown.append(
            {
                "number": row.number,
                "games": selected,
                "hits": hits,
                "baseline_hits": baseline_hits,
            }
        )
    comparisons = len(rows) * quantity
    return {
        "mode": mode,
        "requested_range": {"start": start_contest, "end": end_contest},
        "effective_range": {"start": rows[0].number, "end": rows[-1].number},
        "draw_count": len(rows),
        "missing_count": end_contest - start_contest + 1 - len(rows),
        "game_count": quantity,
        "comparisons": comparisons,
        "distribution": distribution,
        "avg_hits": round(
            sum(h * count for h, count in distribution.items()) / comparisons, 4
        ),
        "baseline": {
            "distribution": baseline_distribution,
            "avg_hits": round(
                sum(h * count for h, count in baseline_distribution.items())
                / comparisons,
                4,
            ),
            "comparisons": comparisons,
        },
        "config": {
            "seed": seed,
            "seed_policy": "single local RNG, ascending stored contest number",
            "training_window": None,
        },
        "contests": breakdown,
    }


def stored_backtest(
    start_contest, end_contest, mode, games=None, quantity=None, seed=None
):
    from results.models import Contest

    validate_config(start_contest, end_contest, mode, games, quantity, seed)
    rows = list(
        Contest.objects.filter(
            number__gte=start_contest, number__lte=end_contest
        ).order_by("number")[:201]
    )
    return evaluate(rows, start_contest, end_contest, mode, games, quantity, seed)
