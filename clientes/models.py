from django.conf import settings
from django.db import models


class Cliente(models.Model):
    """FEAT-01: Ficha de Cliente Unica -- memoria compartida, no vigilancia."""

    class Segmento(models.TextChoices):
        CONSUMO = "CONSUMO", "Consumo / mostrador"
        CORP_MAYOR = "CORP_MAYOR", "Corporativo por mayor"
        CORP_GIRO = "CORP_GIRO", "Corporativo mismo giro"

    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    segmento = models.CharField(max_length=20, choices=Segmento.choices, default=Segmento.CONSUMO)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    """Un cliente casi siempre tiene mas de un vehiculo -- se modela aparte."""

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="vehiculos")
    placa = models.CharField(max_length=20)
    modelo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.placa} ({self.modelo})"


class Interaccion(models.Model):
    """
    FEAT-02: Historial de Interacciones Visible al Equipo.
    Evidencia: el handoff verbal/anotado entre companeras que encontramos
    en las entrevistas -- esto es lo que lo reemplaza.
    """

    class Canal(models.TextChoices):
        WHATSAPP = "WHATSAPP", "WhatsApp"
        LLAMADA = "LLAMADA", "Llamada"
        MOSTRADOR = "MOSTRADOR", "Mostrador"

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="interacciones")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    canal = models.CharField(max_length=20, choices=Canal.choices)
    nota = models.CharField(max_length=280)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.cliente} - {self.get_canal_display()} ({self.fecha:%Y-%m-%d})"
