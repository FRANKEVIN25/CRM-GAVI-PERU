from django.db import models
from django.db.models import Q

from clientes.telefonos import normalizar_e164


class Sede(models.Model):
    """Canal de atencion: cada numero de WhatsApp pertenece a una sede."""
    nombre = models.CharField(max_length=100, unique=True)
    telefono_whatsapp = models.CharField(max_length=20, blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class NumeroWhatsApp(models.Model):
    class Proveedor(models.TextChoices):
        SIN_INTEGRAR = "SIN_INTEGRAR", "Sin integrar"
        META_CLOUD_API = "META_CLOUD_API", "Meta Cloud API"
        TWILIO = "TWILIO", "Twilio"

    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="numeros_whatsapp")
    telefono = models.CharField(max_length=16, db_index=True)
    proveedor = models.CharField(max_length=20, choices=Proveedor.choices, default=Proveedor.SIN_INTEGRAR)
    proveedor_numero_id = models.CharField(max_length=100, blank=True)
    proveedor_cuenta_id = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["proveedor", "proveedor_numero_id"], condition=~Q(proveedor_numero_id=""),
                name="numero_whatsapp_identidad_externa_unica_por_proveedor",
            ),
        ]

    def save(self, *args, **kwargs):
        normalizado = normalizar_e164(self.telefono)
        if not normalizado:
            raise ValueError("El número de WhatsApp debe ser válido.")
        self.telefono = normalizado
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.telefono} · {self.sede}"


class Conversacion(models.Model):
    class Estado(models.TextChoices):
        NUEVA = "NUEVA", "Nueva"
        ABIERTA = "ABIERTA", "Abierta"
        PENDIENTE = "PENDIENTE", "Pendiente"
        RESUELTA = "RESUELTA", "Resuelta"

    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="conversaciones")
    numero = models.ForeignKey(NumeroWhatsApp, null=True, blank=True, on_delete=models.PROTECT, related_name="conversaciones")
    lead = models.ForeignKey("oportunidades.Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="conversaciones_whatsapp")
    cliente = models.ForeignKey("clientes.Cliente", null=True, blank=True, on_delete=models.SET_NULL, related_name="conversaciones_whatsapp")
    cotizacion = models.ForeignKey("cotizaciones.Cotizacion", null=True, blank=True, on_delete=models.SET_NULL, related_name="conversaciones_whatsapp")
    oportunidad_actual = models.ForeignKey("oportunidades.Oportunidad", null=True, blank=True, on_delete=models.SET_NULL, related_name="conversaciones_activas")
    telefono = models.CharField(max_length=16, db_index=True)
    nombre_contacto = models.CharField(max_length=150, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.NUEVA)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    proveedor_conversation_id = models.CharField(max_length=100, blank=True, db_index=True)
    ventana_expira_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-actualizado"]
        constraints = [models.UniqueConstraint(fields=["sede", "telefono"], name="conversacion_unica_por_sede_telefono")]

    def __str__(self):
        return f"{self.nombre_contacto or self.telefono} — {self.sede}"


    def save(self, *args, **kwargs):
        normalizado = normalizar_e164(self.telefono)
        if normalizado:
            self.telefono = normalizado
        super().save(*args, **kwargs)


class MensajeWhatsApp(models.Model):
    class Direccion(models.TextChoices):
        ENTRANTE = "ENTRANTE", "Cliente"
        SALIENTE = "SALIENTE", "Equipo"

    class Tipo(models.TextChoices):
        TEXTO = "TEXTO", "Texto"
        IMAGEN = "IMAGEN", "Imagen"
        DOCUMENTO = "DOCUMENTO", "Documento"
        AUDIO = "AUDIO", "Audio"
        VIDEO = "VIDEO", "Video"
        UBICACION = "UBICACION", "Ubicación"
        PLANTILLA = "PLANTILLA", "Plantilla"

    class EstadoEntrega(models.TextChoices):
        ENVIADO = "ENVIADO", "Enviado"
        ENTREGADO = "ENTREGADO", "Entregado"
        LEIDO = "LEIDO", "Leído"
        FALLIDO = "FALLIDO", "Fallido"

    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name="mensajes")
    direccion = models.CharField(max_length=10, choices=Direccion.choices)
    contenido = models.TextField()
    leido = models.BooleanField(default=False)
    proveedor_message_id = models.CharField(max_length=150, blank=True)
    tipo = models.CharField(max_length=12, choices=Tipo.choices, default=Tipo.TEXTO)
    estado_entrega = models.CharField(max_length=12, choices=EstadoEntrega.choices, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado"]
        constraints = [
            models.UniqueConstraint(
                fields=["conversacion", "proveedor_message_id"], condition=~Q(proveedor_message_id=""),
                name="mensaje_whatsapp_idempotente_por_proveedor",
            ),
        ]


class AgenteNumero(models.Model):
    """
    Controla quién puede ver/responder un número (acceso a la bandeja),
    separado de quién es dueño comercial de un lead nuevo (eso lo resuelve
    AsignacionResponsabilidad). M:N con metadata: un agente puede cubrir
    varios números y un número puede tener varios agentes.
    """

    class Rol(models.TextChoices):
        TITULAR = "titular", "Titular / Ventas"
        SOPORTE = "soporte", "Soporte / Backup"
        SUPERVISOR = "supervisor", "Supervisor"

    agente = models.ForeignKey(
        "usuarios.Agente", on_delete=models.CASCADE, related_name="numeros_asignados"
    )
    numero = models.ForeignKey(
        NumeroWhatsApp, on_delete=models.CASCADE, related_name="agentes_asignados"
    )
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.TITULAR)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("agente", "numero")

    def __str__(self):
        return f"{self.agente} → {self.numero} ({self.get_rol_display()})"


class PlantillaMensaje(models.Model):
    """Plantillas aprobadas de WhatsApp Business (saludo, cotización lista, recordatorio)."""

    nombre = models.CharField(max_length=100, unique=True)
    categoria = models.CharField(max_length=30)
    cuerpo = models.TextField()
    variables = models.JSONField(default=list, help_text="Lista de nombres de variables en el cuerpo.")
    aprobada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} ({'aprobada' if self.aprobada else 'pendiente'})"


class AdjuntoWhatsApp(models.Model):
    mensaje = models.ForeignKey(MensajeWhatsApp, on_delete=models.CASCADE, related_name="adjuntos")
    proveedor_media_id = models.CharField(max_length=150, blank=True)
    url_temporal = models.TextField(blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    nombre_archivo = models.CharField(max_length=255, blank=True)
    tamano_bytes = models.PositiveIntegerField(null=True, blank=True)


class EventoWebhookWhatsApp(models.Model):
    numero = models.ForeignKey(NumeroWhatsApp, null=True, blank=True, on_delete=models.SET_NULL)
    proveedor = models.CharField(max_length=20, choices=NumeroWhatsApp.Proveedor.choices)
    evento_id_proveedor = models.CharField(max_length=150, blank=True, db_index=True)
    payload_hash = models.CharField(max_length=64, unique=True)
    payload = models.JSONField()
    recibido_en = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)
    error = models.TextField(blank=True)
