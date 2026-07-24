"""
Seed de datos de desarrollo para el CRM GAVI PERU.
Uso: python manage.py seed

Crea empresas y contactos (personas naturales) representativos
del mercado de repuestos automotrices en Lima.
Es idempotente: volver a correrlo no duplica datos.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from clientes.models import Cliente, Vehiculo

Usuario = get_user_model()

EMPRESAS = [
    {"nombre": "Taller Mecánico San Martín", "telefono": "014512300", "ruc": "20501234561", "segmento": "TALLER"},
    {"nombre": "Repuestos El Inca S.A.C.", "telefono": "014756800", "ruc": "20501234562", "segmento": "DISTRIBUIDOR"},
    {"nombre": "Automotriz Los Olivos E.I.R.L.", "telefono": "014234500", "ruc": "20501234563", "segmento": "TALLER"},
    {"nombre": "Flota Rápida Perú S.A.", "telefono": "014890100", "ruc": "20501234564", "segmento": "FLOTA"},
    {"nombre": "Seguros La Positiva", "telefono": "016000000", "ruc": "20501234565", "segmento": "SEGUROS"},
    {"nombre": "Concesionario Chery Lima", "telefono": "014123456", "ruc": "20501234566", "segmento": "CONCESIONARIO"},
    {"nombre": "Taller Norte Express", "telefono": "014999111", "ruc": "20501234567", "segmento": "TALLER"},
    {"nombre": "Distribuidora Central Motors", "telefono": "014555666", "ruc": "20501234568", "segmento": "DISTRIBUIDOR"},
    {"nombre": "Municipalidad de San Borja", "telefono": "016187000", "ruc": "20131369981", "segmento": "GOBIERNO"},
    {"nombre": "Delivery Express Lima S.A.C.", "telefono": "014777888", "ruc": "20501234570", "segmento": "FLOTA"},
]

CONTACTOS = [
    {
        "nombre": "Carlos Quispe Mamani",
        "telefono": "987654321",
        "segmento": "TALLER",
        "etapa_ciclo": "CLIENTE",
        "estado_lead": None,
        "empresa": "Taller Mecánico San Martín",
        "vehiculos": [("ABC-123", "Chery Tiggo 4")],
    },
    {
        "nombre": "María Condori Flores",
        "telefono": "976543210",
        "segmento": "MOSTRADOR",
        "etapa_ciclo": "LEAD",
        "estado_lead": "EN_CONTACTO",
        "empresa": None,
        "vehiculos": [("XYZ-456", "JAC S3")],
    },
    {
        "nombre": "Jorge Tarazona Rivas",
        "telefono": "965432109",
        "segmento": "DISTRIBUIDOR",
        "etapa_ciclo": "RECURRENTE",
        "estado_lead": None,
        "empresa": "Repuestos El Inca S.A.C.",
        "vehiculos": [],
    },
    {
        "nombre": "Ana Lucía Vargas",
        "telefono": "954321098",
        "segmento": "MOSTRADOR",
        "etapa_ciclo": "PROSPECTO",
        "estado_lead": "NUEVO",
        "empresa": None,
        "vehiculos": [("DEF-789", "Changan CS35")],
    },
    {
        "nombre": "Roberto Huanca Ticona",
        "telefono": "943210987",
        "segmento": "TALLER",
        "etapa_ciclo": "CLIENTE",
        "estado_lead": None,
        "empresa": "Automotriz Los Olivos E.I.R.L.",
        "vehiculos": [("GHI-012", "Chery QQ"), ("JKL-345", "Chery Arrizo 5")],
    },
    {
        "nombre": "Lisseth Ríos Castillo",
        "telefono": "932109876",
        "segmento": "FLOTA",
        "etapa_ciclo": "LEAD",
        "estado_lead": "CALIFICADO",
        "empresa": "Delivery Express Lima S.A.C.",
        "vehiculos": [],
    },
    {
        "nombre": "Miguel Ángel Soto",
        "telefono": "921098765",
        "segmento": "MOSTRADOR",
        "etapa_ciclo": "LEAD",
        "estado_lead": "NUEVO",
        "empresa": None,
        "vehiculos": [("MNO-678", "JAC J7")],
    },
    {
        "nombre": "Patricia Espinoza Núñez",
        "telefono": "910987654",
        "segmento": "SEGUROS",
        "etapa_ciclo": "CLIENTE",
        "estado_lead": None,
        "empresa": "Seguros La Positiva",
        "vehiculos": [],
    },
    {
        "nombre": "David Ccallo Apaza",
        "telefono": "909876543",
        "segmento": "TALLER",
        "etapa_ciclo": "LEAD",
        "estado_lead": "NO_CALIFICADO",
        "empresa": None,
        "vehiculos": [("PQR-901", "Changan CS75")],
    },
    {
        "nombre": "Gabriela Torres Mendoza",
        "telefono": "998877665",
        "segmento": "CONCESIONARIO",
        "etapa_ciclo": "RECURRENTE",
        "estado_lead": None,
        "empresa": "Concesionario Chery Lima",
        "vehiculos": [],
    },
    {
        "nombre": "Fernando Lazo Herrera",
        "telefono": "987766554",
        "segmento": "MOSTRADOR",
        "etapa_ciclo": "PROSPECTO",
        "estado_lead": "NUEVO",
        "empresa": None,
        "vehiculos": [("STU-234", "Chery Tiggo 7 Pro")],
    },
    {
        "nombre": "Rosa Pilco Mamani",
        "telefono": "976655443",
        "segmento": "GOBIERNO",
        "etapa_ciclo": "CLIENTE",
        "estado_lead": None,
        "empresa": "Municipalidad de San Borja",
        "vehiculos": [],
    },
]


class Command(BaseCommand):
    help = "Carga datos de desarrollo representativos para GAVI PERU."

    def handle(self, *args, **options):
        # Usuario base para registros
        admin, _ = Usuario.objects.get_or_create(
            username="admin_seed",
            defaults={"first_name": "Admin", "last_name": "Seed", "is_staff": True},
        )
        if _:
            admin.set_password("gavi2026")
            admin.save()
            self.stdout.write(self.style.SUCCESS("  Usuario admin_seed creado (pass: gavi2026)"))

        # Empresas
        empresa_map = {}
        for datos in EMPRESAS:
            emp, created = Cliente.objects.get_or_create(
                ruc=datos["ruc"],
                defaults={
                    "nombre": datos["nombre"],
                    "telefono": datos["telefono"],
                    "tipo_entidad": Cliente.TipoEntidad.EMPRESA,
                    "segmento": datos["segmento"],
                    "etapa_ciclo": Cliente.EtapaCiclo.CLIENTE,
                    "creado_por": admin,
                },
            )
            empresa_map[datos["nombre"]] = emp
            self.stdout.write(f"  {'[+]' if created else '[ ]'} Empresa: {emp.nombre}")

        # Contactos
        for datos in CONTACTOS:
            empresa = empresa_map.get(datos["empresa"]) if datos["empresa"] else None
            contacto, created = Cliente.objects.get_or_create(
                telefono=datos["telefono"],
                defaults={
                    "nombre": datos["nombre"],
                    "tipo_entidad": Cliente.TipoEntidad.NATURAL,
                    "segmento": datos["segmento"],
                    "etapa_ciclo": datos["etapa_ciclo"],
                    "estado_lead": datos["estado_lead"],
                    "empresa_principal": empresa,
                    "creado_por": admin,
                },
            )
            for placa, modelo in datos.get("vehiculos", []):
                Vehiculo.objects.get_or_create(
                    cliente=contacto,
                    placa=placa,
                    defaults={"modelo": modelo, "creado_por": admin},
                )
            self.stdout.write(f"  {'[+]' if created else '[ ]'} Contacto: {contacto.nombre}")

        self.stdout.write(self.style.SUCCESS("\nSeed completado."))
