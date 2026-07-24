from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class TareaQuerySet(models.QuerySet):
    def marcar_vencidas(self):
        """Actualiza a VENCIDA toda tarea PENDIENTE cuya fecha ya pasó."""
        return self.filter(
            estado=Tarea.Estado.PENDIENTE,
            fecha_vencimiento__lt=timezone.now(),
        ).update(estado=Tarea.Estado.VENCIDA)


class Tarea(models.Model):
    """
    Acción futura pendiente. Reemplaza a Seguimiento con un modelo más rico
    alineado al modelo de Tasks de HubSpot.

    Al completarse, genera automáticamente una Actividad en el timeline del
    Lead u Oportunidad asociado (ver tareas/services.py).
    """

    class Tipo(models.TextChoices):
        LLAMADA = "llamada", "Llamada"
        CORREO = "correo", "Correo"
        REUNION = "reunion", "Reunión"
        OTRO = "otro", "Otro"

    class Prioridad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        COMPLETADA = "COMPLETADA", "Completada"
        VENCIDA = "VENCIDA", "Vencida"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    objeto = GenericForeignKey("content_type", "object_id")

    titulo = models.CharField(max_length=150)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.OTRO)
    prioridad = models.CharField(max_length=5, choices=Prioridad.choices, default=Prioridad.MEDIA)
    notas = models.TextField(blank=True)
    fecha_vencimiento = models.DateTimeField()
    asignada_a = models.ForeignKey(
        "usuarios.Agente", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tareas_asignadas",
    )
    creada_por = models.ForeignKey(
        "usuarios.Agente", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="tareas_creadas",
    )
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    objects = TareaQuerySet.as_manager()

    class Meta:
        ordering = ["fecha_vencimiento"]
        indexes = [
            models.Index(fields=["content_type", "object_id"], name="tarea_objeto_idx"),
            models.Index(fields=["estado", "fecha_vencimiento"], name="tarea_estado_fecha_idx"),
        ]

    def __str__(self):
        return self.titulo
