from django.db import models


class Sede(models.Model):
    """Canal de atencion: cada numero de WhatsApp pertenece a una sede."""
    nombre = models.CharField(max_length=100, unique=True)
    telefono_whatsapp = models.CharField(max_length=20, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Conversacion(models.Model):
    class Estado(models.TextChoices):
        NUEVA = "NUEVA", "Nueva"
        ABIERTA = "ABIERTA", "Abierta"
        PENDIENTE = "PENDIENTE", "Pendiente"
        RESUELTA = "RESUELTA", "Resuelta"

    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="conversaciones")
    cliente = models.ForeignKey("clientes.Cliente", null=True, blank=True, on_delete=models.SET_NULL, related_name="conversaciones_whatsapp")
    cotizacion = models.ForeignKey("cotizaciones.Cotizacion", null=True, blank=True, on_delete=models.SET_NULL, related_name="conversaciones_whatsapp")
    telefono = models.CharField(max_length=20, db_index=True)
    nombre_contacto = models.CharField(max_length=150, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.NUEVA)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-actualizado"]
        constraints = [models.UniqueConstraint(fields=["sede", "telefono"], name="conversacion_unica_por_sede_telefono")]

    def __str__(self):
        return f"{self.nombre_contacto or self.telefono} — {self.sede}"


class MensajeWhatsApp(models.Model):
    class Direccion(models.TextChoices):
        ENTRANTE = "ENTRANTE", "Cliente"
        SALIENTE = "SALIENTE", "Equipo"

    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name="mensajes")
    direccion = models.CharField(max_length=10, choices=Direccion.choices)
    contenido = models.TextField()
    leido = models.BooleanField(default=False)
    proveedor_message_id = models.CharField(max_length=150, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]
