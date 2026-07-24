"""
Seed de Cotizaciones para el CRM GAVI PERU.
Uso: python manage.py seed_cotizaciones

Prerequisitos:
  python manage.py seed_users
  python manage.py seed
  python manage.py seed_pipeline
  python manage.py seed_oportunidades

Crea cotizaciones enlazadas a las Oportunidades existentes, en estados
variados para poblar el tablero Kanban del vendedor.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from cotizaciones.models import Cotizacion
from oportunidades.models import Lead, Oportunidad

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Carga cotizaciones de desarrollo para GAVI PERU."

    def handle(self, *args, **options):
        try:
            karina = Usuario.objects.get(username="karina_v")
            isabel = Usuario.objects.get(username="isabel_r")
        except Usuario.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                "Usuarios no encontrados. Corre primero: seed_users"
            ))
            return

        # Cotizaciones por oportunidad. Si la oportunidad no existe se omite.
        COTIZACIONES = [
            {
                "lead_telefono": "987001001",
                "usuario": karina,
                "descripcion": "Juego frenos delanteros Chery Tiggo 4: pastillas (x4) + discos (x2)",
                "codigo_producto": "FRE-CT4-001",
                "descuento_pct": 0,
                "estado": Cotizacion.Estado.ENVIADA,
            },
            {
                "lead_telefono": "987001002",
                "usuario": isabel,
                "descripcion": "Kit suspensión JAC S3: amortiguadores x4 + muelles x4 — 3 unidades",
                "codigo_producto": "SUS-JS3-KIT",
                "descuento_pct": 5,
                "estado": Cotizacion.Estado.CONFIRMADA,
            },
            {
                "lead_telefono": "987001004",
                "usuario": karina,
                "descripcion": "Revisión técnica preventiva — 12 vehículos JAC. Incluye filtros y líquidos.",
                "codigo_producto": "SERV-JAC-FLEET",
                "descuento_pct": 8,
                "estado": Cotizacion.Estado.ENVIADA,
            },
            {
                "lead_telefono": "987001005",
                "usuario": karina,
                "descripcion": "Pastillas freno Chery QQ juego completo (delantera + trasera)",
                "codigo_producto": "FRE-CQQ-002",
                "descuento_pct": 0,
                "estado": Cotizacion.Estado.CONVERTIDA,
            },
            {
                "lead_telefono": "987001006",
                "usuario": isabel,
                "descripcion": "Repuestos motor Chery Tiggo 7: kit distribución x5 + filtros x5",
                "codigo_producto": "MOT-CT7-KIT",
                "descuento_pct": 10,
                "estado": Cotizacion.Estado.PERDIDA,
            },
            {
                "lead_telefono": "987001009",
                "usuario": isabel,
                "descripcion": "Par amortiguadores delanteros JAC J7 originales",
                "codigo_producto": "SUS-JJ7-AMO",
                "descuento_pct": 0,
                "estado": Cotizacion.Estado.ENVIADA,
            },
            {
                "lead_telefono": "987001010",
                "usuario": karina,
                "descripcion": "Pedido mensual Changan CS75: filtros aceite x10, filtros aire x5, bujías x20",
                "codigo_producto": "STOCK-CS75-MES",
                "descuento_pct": 7,
                "estado": Cotizacion.Estado.CONFIRMADA,
            },
        ]

        for datos in COTIZACIONES:
            try:
                lead = Lead.objects.get(telefono=datos["lead_telefono"])
                oportunidad = lead.oportunidades.first()
            except Lead.DoesNotExist:
                self.stdout.write(f"  [!] Lead {datos['lead_telefono']} no encontrado, omitido.")
                continue

            # Buscar el cliente a través del lead
            cliente = lead.cliente
            if not cliente:
                self.stdout.write(f"  [!] Lead {lead} sin Cliente vinculado, omitido.")
                continue

            existente = Cotizacion.objects.filter(
                oportunidad=oportunidad,
                descripcion_repuesto=datos["descripcion"],
            ).first()

            if existente:
                self.stdout.write(f"  [ ] Cotizacion ya existe: {existente}")
                continue

            cotizacion = Cotizacion.objects.create(
                cliente=cliente,
                oportunidad=oportunidad,
                usuario=datos["usuario"],
                descripcion_repuesto=datos["descripcion"],
                codigo_producto=datos["codigo_producto"],
                descuento_pct=datos["descuento_pct"],
                estado=datos["estado"],
                vigente=datos["estado"] not in (
                    Cotizacion.Estado.CONVERTIDA, Cotizacion.Estado.PERDIDA
                ),
            )
            self.stdout.write(f"  [+] Cotizacion: {cotizacion.get_estado_display()} — {cotizacion.descripcion_repuesto[:50]}")

        self.stdout.write(self.style.SUCCESS("\nSeed de cotizaciones completado."))
