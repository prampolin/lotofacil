from datetime import datetime

from results.models import Contest


def save_contest(data):
    if not isinstance(data, dict) or type(data.get("numero")) is not int:
        raise ValueError("Número de concurso inválido.")
    if not isinstance(data.get("listaDezenas"), list) or any(
        not (type(value) is int or isinstance(value, str) and value.isdecimal())
        for value in data["listaDezenas"]
    ):
        raise ValueError("Dezenas inválidas.")
    number = data["numero"]

    draw_date = datetime.strptime(data["dataApuracao"], "%d/%m/%Y").date()

    numbers = sorted(int(value) for value in data["listaDezenas"])

    contest = Contest.objects.filter(number=number).first()

    if contest is None:
        contest = Contest(number=number)

    contest.draw_date = draw_date
    contest.numbers = numbers

    contest.full_clean()

    created = contest.pk is None

    contest.save()

    return contest, created
