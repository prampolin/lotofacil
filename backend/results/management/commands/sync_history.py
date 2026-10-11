import math
import time
from itertools import islice

import requests
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from results.models import Contest, SyncExecution
from results.services.import_lock import serialized_import

BASE_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"


class Command(BaseCommand):
    help = "Sincroniza o histórico da Lotofácil em lotes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            type=int,
            default=1,
            help="Primeiro concurso a considerar",
        )

        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Quantidade de concursos por lote",
        )

        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Quantidade máxima de concursos por execução",
        )

        parser.add_argument(
            "--delay",
            type=float,
            default=1.0,
            help="Intervalo entre importações, em segundos",
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula a sincronização sem importar dados",
        )

    @serialized_import
    def handle(self, *args, **options):
        start = options["start"]
        batch_size = options["batch_size"]
        limit = options["limit"]
        delay = options["delay"]
        dry_run = options["dry_run"]

        # Validação dos parâmetros
        if start < 1:
            raise CommandError("--start deve ser positivo.")

        if not 1 <= batch_size <= 100:
            raise CommandError("--batch-size deve estar entre 1 e 100.")

        if not 1 <= limit <= 100:
            raise CommandError("--limit deve estar entre 1 e 100.")

        if not math.isfinite(delay) or delay < 1:
            raise CommandError("--delay deve ser de pelo menos 1 segundo.")

        # Consulta o último concurso informado pela Caixa
        try:
            response = requests.get(
                BASE_URL,
                timeout=20,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

            latest = response.json()["numero"]
            if type(latest) is not int or not 1 <= latest <= 2147483647:
                raise ValueError("Número de concurso inválido.")

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            raise CommandError(
                f"Não foi possível consultar a Caixa: {error}"
            ) from error

        if start > latest:
            raise CommandError(
                f"O início {start} é maior que o último concurso {latest}."
            )

        # Identifica os concursos existentes
        existing = set(
            Contest.objects.filter(
                number__gte=start,
                number__lte=latest,
            ).values_list("number", flat=True)
        )

        # Identifica os concursos ausentes
        missing_count = latest - start + 1 - len(existing)
        missing = (
            number for number in range(start, latest + 1) if number not in existing
        )

        self.stdout.write(f"Último concurso informado: {latest}")
        self.stdout.write(f"Concursos existentes: {len(existing)}")
        self.stdout.write(f"Concursos ausentes: {missing_count}")

        # Limita a quantidade por execução
        selected = list(islice(missing, limit))

        self.stdout.write(f"Concursos selecionados: {len(selected)}")

        # Simulação: não altera o banco
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS("Simulação concluída. Nenhum dado foi alterado.")
            )
            return

        # Nenhum concurso pendente
        if not selected:
            self.stdout.write(
                self.style.SUCCESS("Nenhum concurso pendente neste intervalo.")
            )
            return

        # Registra o início da sincronização
        execution = SyncExecution.objects.create(
            start_contest=selected[0],
            end_contest=selected[-1],
            status="running",
        )

        # Organiza os concursos selecionados em lotes
        batches = [
            selected[i : i + batch_size] for i in range(0, len(selected), batch_size)
        ]

        processed = 0

        try:
            # Também respeita o intervalo após a consulta ao último concurso.
            time.sleep(delay)
            for index, batch in enumerate(batches, start=1):
                self.stdout.write(
                    f"Lote {index}/{len(batches)}: {len(batch)} concursos"
                )

                for number in batch:
                    try:
                        call_command(
                            "import_history",
                            start=number,
                            end=number,
                            delay=delay,
                        )

                    except CommandError as error:
                        raise CommandError(
                            f"Sincronização interrompida no concurso {number}: {error}"
                        ) from error

                    processed += 1

                    # Atualiza o progresso no PostgreSQL
                    execution.processed = processed
                    execution.save(update_fields=["processed"])

                    # Pausa entre as importações
                    if processed < len(selected):
                        time.sleep(delay)

            execution.status = "completed"
            execution.finished_at = timezone.now()
            execution.save(update_fields=["status", "finished_at", "processed"])

        except (Exception, KeyboardInterrupt) as error:
            # Registra falhas sem apagar o progresso anterior
            execution.status = "failed"
            execution.finished_at = timezone.now()
            execution.error_message = str(error) or type(error).__name__

            try:
                execution.save(
                    update_fields=[
                        "status",
                        "finished_at",
                        "error_message",
                        "processed",
                    ]
                )
            except Exception as logging_error:
                self.stderr.write(
                    f"Falha adicional ao registrar execução: {logging_error}"
                )
            raise

        self.stdout.write(
            self.style.SUCCESS(
                f"Sincronização concluída! Concursos processados: {processed}"
            )
        )
