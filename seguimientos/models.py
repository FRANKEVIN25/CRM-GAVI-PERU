from django.conf import settings
from django.db import models

from clientes.models import Cliente
from cotizaciones.models import Cotizacion


class Seguimiento(models.Model):
    """
    FEAT-04: Recordatorio de Seguimiento Centralizado.
    Evidencia: los 5 metodos distintos de recordar un "te confirmo manana"
    (agenda fisica, WhatsApp sin leer, mapeo mental) -- esto los reemplaza.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CUMPLIDO = "CUMPLIDO", "Cumplido"
        VENCIDO = "VENCIDO", "Vencido"

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="seguimientos")
    cotizacion = models.ForeignKey(
        Cotizacion, on_delete=models.SET_NULL, null=True, blank=True, related_name="seguimientos"
    )
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha_recordatorio = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)

    class Meta:
        ordering = ["fecha_recordatorio"]

    def __str__(self):
        return f"Seguimiento a {self.cliente} - {self.fecha_recordatorio:%Y-%m-%d %H:%M}"
