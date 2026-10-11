import math
import time

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from results.management.commands.import_contests import TransientImportError
from results.models import Contest
from results.services.import_lock import serialized_import


class Command(BaseCommand):
    help = "Importa um intervalo de concursos da Lotofácil"

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, required=True)
        parser.add_argument("--end", type=int, required=True)
        parser.add_argument("--delay", type=float, default=1.0)

    @serialized_import
    def handle(self, *args, **options):
        start = options["start"]
        end = options["end"]
        delay = options["delay"]

        if start < 1 or end < start:
            raise CommandError("Intervalo de concursos inválido.")

        if not math.isfinite(delay) or delay < 1:
            raise CommandError("Utilize um intervalo mínimo de 1 segundo.")

        if end - start + 1 > 100:
            raise CommandError("Importe no máximo 100 concursos por execução.")

        imported = 0
        skipped = 0

        for number in range(start, end + 1):
            # Ignora concursos já cadastrados
            if Contest.objects.filter(number=number).exists():
                self.stdout.write(f"Concurso {number} já existe. Ignorando.")
                skipped += 1
                continue

            # Tenta importar até três vezes
            for attempt in range(1, 4):
                try:
                    call_command("import_contests", number=number)
                    imported += 1
                    break

                except TransientImportError as error:
                    self.stderr.write(
                        f"Concurso {number}: tentativa {attempt}/3 falhou: {error}"
                    )

                    if attempt == 3:
                        raise CommandError(
                            f"Falha após 3 tentativas no concurso {number}."
                        ) from error

                    if error.retry_after > 300:
                        raise CommandError(
                            "Retry-After excede 300 segundos; retome mais tarde."
                        ) from error
                    time.sleep(max(delay, attempt * 2, error.retry_after))

                except CommandError:
                    raise

            # Pausa entre as requisições
            if number < end:
                time.sleep(delay)

        self.stdout.write(
            self.style.SUCCESS(
                f"Concluído! Importados: {imported} | Ignorados: {skipped}"
            )
        )
