from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
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
    # Probabilidad de cierre asignada a esta etapa (0–100).
    # Base del forecast: valor_estimado × probabilidad_pct / 100 = valor ponderado.
    # Las etapas GANADA=100 y PERDIDA=0 son invariantes de negocio.
    probabilidad_pct = models.PositiveSmallIntegerField(
        default=0,
        help_text="Probabilidad de cierre en esta etapa (0–100). Usado en el forecast del dashboard.",
    )

    class Meta:
        ordering = ["pipeline", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["pipeline", "orden"], name="etapa_orden_unico_por_pipeline"),
            models.UniqueConstraint(fields=["pipeline", "nombre"], name="etapa_nombre_unico_por_pipeline"),
        ]

    @property
    def es_cierre_ganado(self):
        return self.tipo == self.Tipo.GANADA

    @property
    def es_cierre_perdido(self):
        return self.tipo == self.Tipo.PERDIDA

    def __str__(self):
        return f"{self.pipeline}: {self.nombre}"


class Lead(models.Model):
    """
    Contacto comercial entrante. Puede o no estar vinculado a un Cliente
    registrado. Es el punto de entrada del funnel: un Lead sin conversión
    es una oportunidad perdida antes de empezar.
    """

    class Origen(models.TextChoices):
        WHATSAPP_DIRECTO = "whatsapp_directo", "WhatsApp directo"
        CATALOGO_RFQ = "catalogo_rfq", "RFQ desde catálogo"
        REFERIDO = "referido", "Referido"
        MANUAL = "manual", "Ingreso manual"

    nombre_contacto = models.CharField(max_length=150, blank=True)
    telefono = models.CharField(max_length=20, db_index=True)
    telefono_normalizado = models.CharField(max_length=16, null=True, blank=True, db_index=True)
    email = models.EmailField(blank=True)
    cliente = models.ForeignKey(
        "clientes.Cliente", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="leads",
        help_text="Se vincula cuando el lead coincide con un cliente ya registrado.",
    )
    marca_interes = models.ForeignKey(
        "clientes.Marca", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="leads",
    )
    origen = models.CharField(max_length=20, choices=Origen.choices, default=Origen.MANUAL)
    agente_asignado = models.ForeignKey(
        "usuarios.Agente", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="leads_asignados",
    )
    creado = models.DateTimeField(auto_now_add=True)
    primera_respuesta = models.DateTimeField(
        null=True, blank=True,
        help_text="KPI: tiempo hasta la primera respuesta del equipo.",
    )

    class Meta:
        ordering = ["-creado"]

    def save(self, *args, **kwargs):
        from clientes.telefonos import normalizar_e164
        self.telefono_normalizado = normalizar_e164(self.telefono)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_contacto or self.telefono


class Oportunidad(models.Model):
    """
    Trato comercial. Las cotizaciones son ofertas dentro de esta entidad.
    Se crea desde un Lead; el cierre se hace únicamente via services.py.
    """

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="oportunidades")
    pipeline = models.ForeignKey(Pipeline, on_delete=models.PROTECT, related_name="oportunidades")
    etapa_actual = models.ForeignKey(Etapa, on_delete=models.PROTECT, related_name="oportunidades")
    titulo = models.CharField(max_length=150, blank=True)
    valor_estimado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_cierre_estimada = models.DateField(null=True, blank=True)
    fecha_cierre_real = models.DateTimeField(null=True, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="oportunidades_creadas",
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Contexto del trato: qué necesita, urgencia, condiciones especiales.",
    )
    motivo_perdida = models.CharField(max_length=255, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-actualizado"]
        indexes = [
            models.Index(fields=["lead", "etapa_actual"], name="oportunidad_lead_etapa_idx"),
        ]

    @property
    def estado(self):
        """Estado derivado del tipo de etapa; nunca se puede desincronizar en BD."""
        return self.etapa_actual.tipo

    @property
    def esta_cerrada(self):
        return self.etapa_actual.tipo in (Etapa.Tipo.GANADA, Etapa.Tipo.PERDIDA)

    def __str__(self):
        return self.titulo or f"Oportunidad #{self.pk} — {self.lead}"


class CambioEtapa(models.Model):
    """Historial inmutable de movimientos en el pipeline. Base de la analítica de funnel."""

    oportunidad = models.ForeignKey(Oportunidad, on_delete=models.CASCADE, related_name="historial_etapas")
    etapa_anterior = models.ForeignKey(Etapa, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    etapa_nueva = models.ForeignKey(Etapa, on_delete=models.PROTECT, related_name="+")
    agente = models.ForeignKey(
        "usuarios.Agente", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="cambios_etapa",
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["oportunidad", "timestamp"], name="cambio_opp_fecha_idx"),
        ]


class Actividad(models.Model):
    """
    Log histórico inmutable: nota, llamada, mensaje WA.
    Registra lo que ya ocurrió en el timeline de un Lead u Oportunidad.
    Las acciones futuras pendientes son Tarea (app tareas/), no Actividad.
    """

    class Tipo(models.TextChoices):
        NOTA = "nota", "Nota"
        LLAMADA = "llamada", "Llamada"
        WHATSAPP = "whatsapp", "WhatsApp"

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    objeto = GenericForeignKey("content_type", "object_id")

    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    agente = models.ForeignKey(
        "usuarios.Agente", null=True, on_delete=models.SET_NULL,
        related_name="actividades",
    )
    descripcion = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        indexes = [
            models.Index(fields=["content_type", "object_id"], name="actividad_objeto_idx"),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.objeto} ({self.creado:%Y-%m-%d})"
