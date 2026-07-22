from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    """
    FEAT-00: Autenticacion y Roles Basicos.
    Extiende el usuario estandar de Django (ya trae username, email,
    password hasheado, etc.) y le agrega el rol que define el DAS.
    """

    class Rol(models.TextChoices):
        VENDEDOR   = "VENDEDOR",   "Vendedor"
        TECNICO    = "TECNICO",    "Soporte técnico"   # Mecánico, asesor técnico: ve conversaciones, no pipeline
        SUPERVISOR = "SUPERVISOR", "Supervisor de ventas"  # Ve su equipo, no configura
        GERENTE    = "GERENTE",    "Gerente"           # Reportes y aprobaciones
        ADMIN_CRM  = "ADMIN_CRM",  "Administrador CRM" # Configura pipelines, etapas, plantillas WA

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.VENDEDOR)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"


class Agente(models.Model):
    """
    Perfil operativo CRM del usuario. Separa la identidad de autenticación
    (Usuario) de la capacidad comercial (Agente): límites de carga, número
    de WA propio, estado activo/inactivo sin deshabilitar el login.
    """

    usuario = models.OneToOneField(
        "usuarios.Usuario", on_delete=models.CASCADE, related_name="agente"
    )
    activo = models.BooleanField(default=True)
    max_leads_simultaneos = models.PositiveIntegerField(default=30)
    telefono_whatsapp = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Agente: {self.usuario}"

    
class AsignacionResponsabilidad(models.Model):
    """
    Punto único de ruteo comercial: qué agente atiende cada Marca.
    Deliberadamente general: si mañana se necesita asignar por categoría,
    región o tipo de cliente, se agrega el campo aquí sin romper Lead,
    Oportunidad ni WhatsApp que ya consultan esta tabla.
    """

    marca = models.ForeignKey(
        "clientes.Marca", on_delete=models.CASCADE, related_name="responsables"
    )
    agente = models.ForeignKey(
        Agente, on_delete=models.CASCADE, related_name="responsabilidades"
    )
    prioridad = models.PositiveSmallIntegerField(default=1)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("marca", "agente")
        ordering = ["marca", "prioridad"]

    def __str__(self):
        return f"{self.agente} → {self.marca} (prio {self.prioridad})"

