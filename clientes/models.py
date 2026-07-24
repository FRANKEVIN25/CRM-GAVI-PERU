from django.conf import settings
from django.db import models


class Marca(models.Model):
    """Marca de vehículo (Chery, Changan, JAC, etc.). Punto de ruteo comercial."""

    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    """FEAT-01: Ficha de Cliente Unica -- memoria compartida, no vigilancia."""

    class TipoEntidad(models.TextChoices):
        NATURAL = "NATURAL", "Persona natural"
        EMPRESA = "EMPRESA", "Empresa / RUC"

    class Segmento(models.TextChoices):
        # Canal minorista: comprador final que llega al mostrador.
        MOSTRADOR = "MOSTRADOR", "Mostrador / retail"
        # Talleres mecánicos y de mantenimiento: compradores frecuentes de repuestos.
        TALLER = "TALLER", "Taller mecánico"
        # Distribuidores y mayoristas que revenden los repuestos.
        DISTRIBUIDOR = "DISTRIBUIDOR", "Distribuidor / mayorista"
        # Empresas aseguradoras que derivan vehículos siniestrados a talleres.
        SEGUROS = "SEGUROS", "Aseguradora"
        # Empresas con flota propia: delivery, transporte, taxi, minería, etc.
        FLOTA = "FLOTA", "Empresa con flota"
        # Concesionarios de marcas chinas (Chery, Changan, JAC, etc.).
        CONCESIONARIO = "CONCESIONARIO", "Concesionario"
        # Gobiernos locales, ministerios, entidades del estado con flota pública.
        GOBIERNO = "GOBIERNO", "Entidad de gobierno"

    class EtapaCiclo(models.TextChoices):
        PROSPECTO = "PROSPECTO", "Prospecto"
        LEAD = "LEAD", "Lead"
        CLIENTE = "CLIENTE", "Cliente"
        RECURRENTE = "RECURRENTE", "Recurrente"

    class EstadoLead(models.TextChoices):
        NUEVO = "NUEVO", "Nuevo"
        EN_CONTACTO = "EN_CONTACTO", "En contacto"
        CALIFICADO = "CALIFICADO", "Calificado"
        NO_CALIFICADO = "NO_CALIFICADO", "No calificado"

    # ── Identidad ───────────────────────────────────────────────────────────
    nombre = models.CharField(max_length=150)
    tipo_entidad = models.CharField(
        max_length=10,
        choices=TipoEntidad.choices,
        default=TipoEntidad.NATURAL,
    )
    # Solo para tipo_entidad=EMPRESA. 11 dígitos según SUNAT.
    ruc = models.CharField(max_length=11, blank=True)
    # Una persona natural puede estar vinculada a la empresa que la envía.
    empresa_principal = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contactos",
        limit_choices_to={"tipo_entidad": TipoEntidad.EMPRESA},
    )

    # ── Contacto ────────────────────────────────────────────────────────────
    telefono = models.CharField(max_length=20)
    telefono_normalizado = models.CharField(max_length=16, null=True, blank=True, db_index=True)

    # ── Segmentación comercial ───────────────────────────────────────────────
    # Cómo compra, no quién es (ver docs/clientes-modelo-dominio.md §3.2).
    segmento = models.CharField(max_length=20, choices=Segmento.choices, default=Segmento.MOSTRADOR)

    # ── Ciclo de vida ────────────────────────────────────────────────────────
    # Responde "¿dónde está en la relación total con GAVI?".
    # La transición a CLIENTE la dispara oportunidades/services.py,
    # nunca una edición manual directa.
    etapa_ciclo = models.CharField(
        max_length=12,
        choices=EtapaCiclo.choices,
        default=EtapaCiclo.LEAD,
    )
    # Estado operacional de corto plazo. Solo relevante cuando etapa_ciclo=LEAD.
    estado_lead = models.CharField(
        max_length=14,
        choices=EstadoLead.choices,
        null=True,
        blank=True,
    )

    # ── Auditoría ────────────────────────────────────────────────────────────
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
    marca = models.ForeignKey(Marca, null=True, blank=True, on_delete=models.SET_NULL)
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
