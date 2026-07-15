from django.conf import settings
from django.db import models

from clientes.models import Cliente


class Cotizacion(models.Model):
    """
    FEAT-03: Registro de Cotizaciones con Estado.
    FEAT-06: Trazabilidad de Descuentos (mismo formulario, campo descuento_pct).
    """

    class Estado(models.TextChoices):
        ENVIADA = "ENVIADA", "Enviada"
        CONFIRMADA = "CONFIRMADA", "Confirmada"
        CONVERTIDA = "CONVERTIDA", "Convertida"
        PERDIDA = "PERDIDA", "Perdida"

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="cotizaciones")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion_repuesto = models.TextField()
    # Puente de bajo costo hacia el sistema externo de productos, si algun
    # dia se integra (ver DAS seccion 7). No es una FK a un catalogo real.
    codigo_producto = models.CharField(max_length=50, blank=True)
    descuento_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ENVIADA)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"Cotizacion #{self.pk} - {self.cliente} ({self.get_estado_display()})"
