from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from results.services.contest_service import save_contest
from results.services.import_lock import serialized_import

BASE_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"


class TransientImportError(CommandError):
    """Erro temporário que permite novas tentativas."""

    def __init__(self, message, *, retry_after=0):
        super().__init__(message)
        self.retry_after = retry_after


def retry_after_seconds(value):
    """Parse a server delay without changing the local retry policy."""
    if not isinstance(value, str):
        return 0
    value = value.strip()
    if value.isascii() and value.isdigit():
        # Avoid converting arbitrarily large untrusted integers.
        return int(value) if len(value) < 10 else 301
    try:
        deadline = parsedate_to_datetime(value)
        if deadline.tzinfo is None:
            return 0
        return max(0, (deadline - datetime.now(timezone.utc)).total_seconds())
    except ValueError, TypeError, OverflowError:
        return 0


class Command(BaseCommand):
    help = "Importa concursos da Lotofácil para o PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            type=int,
            help="Número do concurso a importar",
        )

    @serialized_import
    def handle(self, *args, **options):
        number = options["number"]

        if number is not None and number < 1:
            raise CommandError("O concurso deve ser positivo.")

        url = BASE_URL if number is None else f"{BASE_URL}/{number}"

        self.stdout.write(f"Consultando Caixa: {url}")

        try:
            response = requests.get(
                url,
                timeout=20,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

            if number is not None and int(data["numero"]) != number:
                raise CommandError(
                    "A Caixa retornou um concurso diferente do solicitado."
                )

            contest, created = save_contest(data)

        except requests.HTTPError as error:
            status_code = error.response.status_code

            if status_code == 429 or status_code >= 500:
                raise TransientImportError(
                    f"Erro temporário HTTP {status_code}",
                    retry_after=retry_after_seconds(
                        error.response.headers.get("Retry-After")
                    ),
                ) from error

            raise CommandError(f"Erro permanente HTTP {status_code}") from error

        except (requests.Timeout, requests.ConnectionError) as error:
            raise TransientImportError(
                f"Falha temporária de conexão: {error}"
            ) from error

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
            ValidationError,
        ) as error:
            raise CommandError(f"Falha ao importar concurso: {error}") from error

        action = "importado" if created else "atualizado"

        self.stdout.write(
            self.style.SUCCESS(f"Concurso {contest.number} {action} com sucesso!")
        )
