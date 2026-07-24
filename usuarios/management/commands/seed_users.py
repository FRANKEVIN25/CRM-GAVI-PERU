"""
Seed de usuarios y agentes de desarrollo para el CRM GAVI PERU.
Uso: python manage.py seed_users

Crea un conjunto representativo de usuarios por rol con sus perfiles
de Agente. Es idempotente: correrlo de nuevo no duplica nada.

Roles creados:
  - 1 ADMIN_CRM   (configura pipelines y etapas)
  - 1 GERENTE     (ve reportes y aprueba descuentos)
  - 1 SUPERVISOR  (ve su equipo)
  - 3 VENDEDOR    (el equipo operativo de GAVI)
  - 1 TECNICO     (asesor técnico, ve conversaciones)
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from usuarios.models import Agente

Usuario = get_user_model()

# (username, password, first_name, last_name, rol, es_staff, agente?)
USUARIOS = [
    ("admin_crm",   "gavi2026!", "Franklin",  "Gavilan",  "ADMIN_CRM",  True,  False),
    ("gerente",     "gavi2026!", "Carlos",    "Medina",   "GERENTE",    False, False),
    ("supervisor",  "gavi2026!", "Patricia",  "Solis",    "SUPERVISOR", False, True),
    ("karina_v",    "gavi2026!", "Karina",    "Vargas",   "VENDEDOR",   False, True),
    ("isabel_r",    "gavi2026!", "Isabel",    "Ríos",     "VENDEDOR",   False, True),
    ("jose_q",      "gavi2026!", "José",      "Quispe",   "VENDEDOR",   False, True),
    ("tecnico",     "gavi2026!", "Marco",     "Huanca",   "TECNICO",    False, False),
]

# Configuración de agente por username (max_leads, telefono_wa)
AGENTE_CONFIG = {
    "supervisor": (50, "+51999000001"),
    "karina_v":   (30, "+51999000002"),
    "isabel_r":   (30, "+51999000003"),
    "jose_q":     (25, "+51999000004"),
}


class Command(BaseCommand):
    help = "Carga usuarios y agentes de desarrollo para GAVI PERU."

    def handle(self, *args, **options):
        for username, password, first, last, rol, is_staff, crear_agente in USUARIOS:
            usuario, created = Usuario.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "rol": rol,
                    "is_staff": is_staff,
                },
            )
            if created:
                usuario.set_password(password)
                usuario.save()

            self.stdout.write(
                f"  {'[+]' if created else '[ ]'} {rol:12} {usuario.get_full_name()} ({username})"
            )

            if crear_agente:
                config = AGENTE_CONFIG.get(username, (30, ""))
                agente, ag_created = Agente.objects.get_or_create(
                    usuario=usuario,
                    defaults={
                        "activo": True,
                        "max_leads_simultaneos": config[0],
                        "telefono_whatsapp": config[1],
                    },
                )
                if ag_created:
                    self.stdout.write(f"           → Agente creado (max_leads={config[0]})")

        self.stdout.write(self.style.SUCCESS("\nSeed de usuarios completado."))
        self.stdout.write("  Contraseña de todos los usuarios: gavi2026!")
        self.stdout.write("  admin_crm tiene acceso al panel /admin/")
