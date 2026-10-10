from collections import Counter


class DomainError(ValueError):
    """Invalid input or stored data."""


class EmptyDataError(DomainError):
    """No stored draws in the selection."""


def integer(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise DomainError(f"{name} deve estar entre {minimum} e {maximum}.")
    return value


def ticket(numbers):
    if (
        not isinstance(numbers, list)
        or len(numbers) != 15
        or any(type(n) is not int or not 1 <= n <= 25 for n in numbers)
        or len(set(numbers)) != 15
    ):
        raise DomainError("São necessárias 15 dezenas distintas de 1 a 25.")
    return sorted(numbers)


def statistics(contests):
    rows = sorted(contests, key=lambda row: row.number)
    if not rows:
        raise EmptyDataError("Nenhum concurso encontrado.")
    draws = [ticket(row.numbers) for row in rows]
    counts = Counter(n for draw in draws for n in draw)
    per_number = []
    for n in range(1, 26):
        last = next((i for i, draw in enumerate(reversed(draws)) if n in draw), None)
        per_number.append(
            {
                "number": n,
                "count": counts[n],
                "frequency_pct": round(counts[n] / len(draws) * 100, 2),
                "draws_since_last_seen": last,
            }
        )
    per_contest = []
    previous = None
    for row, draw in zip(rows, draws, strict=True):
        odd = sum(n % 2 for n in draw)
        per_contest.append(
            {
                "number": row.number,
                "odd_count": odd,
                "even_count": 15 - odd,
                "sum": sum(draw),
                "consecutive_pairs": sum(
                    b == a + 1 for a, b in zip(draw, draw[1:], strict=False)
                ),
                "repeated_from_previous": None
                if previous is None
                else len(set(draw) & set(previous)),
            }
        )
        previous = draw
    sums = [row["sum"] for row in per_contest]
    repetitions = [row["repeated_from_previous"] for row in per_contest[1:]]
    return {
        "sample_size": len(rows),
        "first_contest": rows[0].number,
        "last_contest": rows[-1].number,
        "numbers": per_number,
        "contests": per_contest,
        "aggregates": {
            "odd_distribution": dict(
                sorted(Counter(row["odd_count"] for row in per_contest).items())
            ),
            "even_distribution": dict(
                sorted(Counter(row["even_count"] for row in per_contest).items())
            ),
            "sum": {
                "min": min(sums),
                "max": max(sums),
                "mean": round(sum(sums) / len(sums), 2),
            },
            "mean_consecutive_pairs": round(
                sum(row["consecutive_pairs"] for row in per_contest) / len(rows), 2
            ),
            "mean_repetitions": round(sum(repetitions) / len(repetitions), 2)
            if repetitions
            else None,
        },
    }


def stored_statistics(window=100, as_of_contest=None):
    from results.models import Contest

    integer(window, "window", 1, 1000)
    queryset = Contest.objects.all()
    if as_of_contest is not None:
        integer(as_of_contest, "as_of_contest", 1, 2147483647)
        queryset = queryset.filter(number__lte=as_of_contest)
    result = statistics(list(queryset.order_by("-number")[:window]))
    return {"window": window, "as_of_contest": as_of_contest, **result}
