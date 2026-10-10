import requests
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from results.services.contest_service import save_contest

BASE_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"


class TransientImportError(CommandError):
    """Erro temporário que permite novas tentativas."""


class Command(BaseCommand):
    help = "Importa concursos da Lotofácil para o PostgreSQL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--number",
            type=int,
            help="Número do concurso a importar",
        )

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
                    f"Erro temporário HTTP {status_code}"
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
