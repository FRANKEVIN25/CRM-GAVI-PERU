from django.conf import settings
from django.db import models


class Cliente(models.Model):
    """FEAT-01: Ficha de Cliente Unica -- memoria compartida, no vigilancia."""

    class Segmento(models.TextChoices):
        CONSUMO = "CONSUMO", "Consumo / mostrador"
        CORPORATIVO = "CORPORATIVO", "Corporativo"
        SEGUROS = "SEGUROS", "Seguros"
        TALLER = "TALLER", "Taller"

    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    telefono_normalizado = models.CharField(max_length=16, null=True, blank=True, db_index=True)
    segmento = models.CharField(max_length=20, choices=Segmento.choices, default=Segmento.CONSUMO)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clientes_creados",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        from .telefonos import normalizar_e164

        self.telefono_normalizado = normalizar_e164(self.telefono)
        super().save(*args, **kwargs)


class Vehiculo(models.Model):
    """Un cliente casi siempre tiene mas de un vehiculo -- se modela aparte."""

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="vehiculos")
    placa = models.CharField(max_length=20)
    modelo = models.CharField(max_length=100, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vehiculos_creados",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.placa} ({self.modelo})"

    def save(self, *args, **kwargs):
        self.placa = (self.placa or "").strip().upper()
        super().save(*args, **kwargs)


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
