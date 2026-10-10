from django.core.exceptions import ValidationError
from django.db import models


class Contest(models.Model):
    number = models.PositiveIntegerField(unique=True)

    draw_date = models.DateField()

    numbers = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-number"]
        verbose_name = "Concurso"
        verbose_name_plural = "Concursos"

    def clean(self):
        super().clean()

        if type(self.number) is not int or self.number < 1:
            raise ValidationError({"number": "O concurso deve ser positivo."})

        if not isinstance(self.numbers, list):
            raise ValidationError({"numbers": "As dezenas devem ser uma lista."})

        if len(self.numbers) != 15:
            raise ValidationError(
                {"numbers": "O concurso deve conter exatamente 15 dezenas."}
            )

        if (
            any(type(n) is not int or n < 1 or n > 25 for n in self.numbers)
            or len(set(self.numbers)) != 15
        ):
            raise ValidationError(
                {"numbers": "As dezenas devem ser únicas e estar entre 1 e 25."}
            )

        self.numbers = sorted(self.numbers)

    def __str__(self):
        return f"Concurso {self.number}"


class SyncExecution(models.Model):
    STATUS_CHOICES = [
        ("running", "Em execução"),
        ("completed", "Concluído"),
        ("failed", "Falhou"),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="running",
    )

    start_contest = models.PositiveIntegerField()
    end_contest = models.PositiveIntegerField()

    processed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Sincronização {self.id} - {self.status}"
