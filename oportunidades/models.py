from django.conf import settings
from django.db import models


class Pipeline(models.Model):
    """Configuración de un proceso comercial, independiente de la cotización."""

    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Etapa(models.Model):
    class Tipo(models.TextChoices):
        EN_PROGRESO = "EN_PROGRESO", "En progreso"
        GANADA = "GANADA", "Ganada"
        PERDIDA = "PERDIDA", "Perdida"

    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name="etapas")
    nombre = models.CharField(max_length=60)
    orden = models.PositiveSmallIntegerField()
    tipo = models.CharField(max_length=16, choices=Tipo.choices, default=Tipo.EN_PROGRESO)

    class Meta:
        ordering = ["pipeline", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["pipeline", "orden"], name="etapa_orden_unico_por_pipeline"),
            models.UniqueConstraint(fields=["pipeline", "nombre"], name="etapa_nombre_unico_por_pipeline"),
        ]

    def __str__(self):
        return f"{self.pipeline}: {self.nombre}"


class Oportunidad(models.Model):
    """Trato comercial. Las cotizaciones son ofertas dentro de esta entidad."""

    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE, related_name="oportunidades")
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT, related_name="oportunidades")
    etapa = models.ForeignKey(Etapa, on_delete=models.PROTECT, related_name="oportunidades")
    titulo = models.CharField(max_length=150, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="oportunidades_creadas",
    )
    cerrada_en = models.DateTimeField(null=True, blank=True)
    motivo_perdida = models.CharField(max_length=255, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-actualizado"]
        indexes = [models.Index(fields=["cliente", "etapa"], name="oportunidad_cliente_etapa_idx")]

    @property
    def estado(self):
        """Estado derivado: no se duplica ni se puede desincronizar en BD."""
        return self.etapa.tipo

    @property
    def esta_cerrada(self):
        return self.etapa.tipo in (Etapa.Tipo.GANADA, Etapa.Tipo.PERDIDA)

    def __str__(self):
        return self.titulo or f"Oportunidad #{self.pk} - {self.cliente}"


class CambioEtapa(models.Model):
    oportunidad = models.ForeignKey(Oportunidad, on_delete=models.CASCADE, related_name="historial_etapas")
    etapa_anterior = models.ForeignKey(Etapa, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    etapa_nueva = models.ForeignKey(Etapa, on_delete=models.PROTECT, related_name="+")
    cambiado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    cambiado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cambiado_en"]
        indexes = [models.Index(fields=["oportunidad", "cambiado_en"], name="cambio_opp_fecha_idx")]
