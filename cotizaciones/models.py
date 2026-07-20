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

    # SCRUM-13: flujo Enviada -> Confirmada -> Convertida/Perdida. Enviada
    # tambien puede pasar directo a Perdida: el hallazgo del 91% de perdida
    # (ver DAS, sintesis de descubrimiento) ocurre sobre todo antes de que
    # el cliente llegue a confirmar, asi que exigir el paso por Confirmada
    # ocultaria justo el dato que el sistema existe para capturar.
    TRANSICIONES = {
        Estado.ENVIADA: (Estado.CONFIRMADA, Estado.PERDIDA),
        Estado.CONFIRMADA: (Estado.CONVERTIDA, Estado.PERDIDA),
        Estado.CONVERTIDA: (),
        Estado.PERDIDA: (),
    }

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="cotizaciones")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    # Tablero del vendedor (FEAT-03 evolucion): "dias desde la ultima
    # actualizacion" necesita un campo propio -- `fecha` es la creacion y
    # nunca cambia, no sirve para detectar cotizaciones estancadas.
    actualizado = models.DateTimeField(auto_now=True)
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

    def siguientes_estados(self):
        return self.TRANSICIONES.get(self.estado, ())

    def puede_transicionar_a(self, nuevo_estado):
        return nuevo_estado in self.siguientes_estados()
