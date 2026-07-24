"""
Seed de Leads y Oportunidades para el CRM GAVI PERU.
Uso: python manage.py seed_oportunidades

Prerequisitos (correr antes):
  python manage.py seed_users
  python manage.py seed_pipeline
  python manage.py seed

Crea leads representativos del mercado de repuestos en Lima y los mueve
por las etapas del pipeline con historial de CambioEtapa. Cubre los
tres escenarios del embudo: en progreso, ganadas y perdidas.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from clientes.models import Cliente
from oportunidades.models import Actividad, CambioEtapa, Etapa, Lead, Oportunidad, Pipeline
from usuarios.models import Agente

Usuario = get_user_model()

# (nombre, telefono, email, origen, etapa_nombre, valor, titulo, descripcion, dias_atras)
# etapa_nombre=None → solo Lead, sin Oportunidad todavía
DATOS = [
    (
        "Luis Paredes Huanca", "987001001", "", "whatsapp_directo",
        "Propuesta Enviada", 1200, "Frenos Chery Tiggo 4 — Taller Paredes",
        "Juego completo de frenos delanteros y traseros. Urgente, el vehículo está inmovilizado.",
        5,
    ),
    (
        "Taller San Borja SAC", "987001002", "tallersanborja@gmail.com", "manual",
        "Negociación", 3500, "Kit suspensión JAC S3 x3 unidades",
        "Taller compra en volumen mensual. Piden 5% de descuento adicional sobre lista.",
        3,
    ),
    (
        "Rosa Mamani Castro", "987001003", "", "whatsapp_directo",
        "Contacto Inicial", 450, "Filtros aceite Changan CS35",
        "Consulta por filtros de aceite y aire. Primera compra, viene referida por Taller Norte.",
        1,
    ),
    (
        "Flota Lima Express", "987001004", "compras@limaexpress.pe", "catalogo_rfq",
        "Calificación", 8900, "Revisión técnica flota 12 vehículos JAC",
        "Flota de delivery. Necesitan mantenimiento programado. Decisión la toma el jefe de flota.",
        7,
    ),
    (
        "Pedro Quispe Torres", "987001005", "", "referido",
        "Cerrado Ganado", 620, "Pastillas freno Chery QQ",
        "Cliente recurrente. Compra cerrada, cotización confirmada y convertida.",
        10,
    ),
    (
        "Importadora Del Norte SRL", "987001006", "ventas@importadoranorte.pe", "manual",
        "Cerrado Perdido", 5200, "Repuestos motor Chery Tiggo 7 x5",
        "Perdido por precio. El cliente encontró proveedor directo en China.",
        14,
    ),
    (
        "Ana Condori Flores", "987001007", "", "whatsapp_directo",
        "Prospección", 300, "Consulta repuestos varios",
        "Primera consulta vía WA. Aún no calificado.",
        0,
    ),
    (
        "Taller Mecánico Rímac", "987001008", "", "referido",
        None, 0, "", "",  # Lead sin Oportunidad aún
        0,
    ),
    (
        "Carlos Benites Soto", "987001009", "", "whatsapp_directo",
        "Contacto Inicial", 780, "Amortiguadores JAC J7 par delantero",
        "El cliente tiene presupuesto aprobado esta semana.",
        2,
    ),
    (
        "Distribuidora Andina EIRL", "987001010", "compras@distribuidoraandina.pe", "manual",
        "Propuesta Enviada", 4100, "Stock repuestos Changan CS75 — pedido mensual",
        "Distribuidor regional. Pedido recurrente cada 30 días.",
        4,
    ),
]

MOTIVOS_PERDIDA = {
    "Cerrado Perdido": "Cliente encontró mejor precio en otro proveedor.",
}


def _etapa(pipeline, nombre):
    return Etapa.objects.get(pipeline=pipeline, nombre=nombre)


def _registrar_progreso(oportunidad, etapa_destino, agente, dias_atras):
    """Simula el historial de movimientos de etapa hasta la etapa actual."""
    pipeline = oportunidad.pipeline
    etapas_en_progreso = list(
        pipeline.etapas.filter(tipo=Etapa.Tipo.EN_PROGRESO).order_by("orden")
    )
    orden_destino = etapa_destino.orden

    etapa_anterior = None
    for etapa in etapas_en_progreso:
        if etapa.orden > orden_destino:
            break
        CambioEtapa.objects.get_or_create(
            oportunidad=oportunidad,
            etapa_nueva=etapa,
            defaults={"etapa_anterior": etapa_anterior, "agente": agente},
        )
        etapa_anterior = etapa

    if etapa_destino.tipo != Etapa.Tipo.EN_PROGRESO:
        CambioEtapa.objects.get_or_create(
            oportunidad=oportunidad,
            etapa_nueva=etapa_destino,
            defaults={"etapa_anterior": etapa_anterior, "agente": agente},
        )


class Command(BaseCommand):
    help = "Carga leads y oportunidades de desarrollo para GAVI PERU."

    def handle(self, *args, **options):
        try:
            pipeline = Pipeline.objects.get(nombre="Venta de Repuestos GAVI")
        except Pipeline.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                "Pipeline no encontrado. Corre primero: python manage.py seed_pipeline"
            ))
            return

        try:
            agente_karina = Agente.objects.get(usuario__username="karina_v")
            agente_isabel = Agente.objects.get(usuario__username="isabel_r")
            admin = Usuario.objects.get(username="admin_seed")
        except (Agente.DoesNotExist, Usuario.DoesNotExist):
            self.stdout.write(self.style.ERROR(
                "Usuarios no encontrados. Corre primero: seed_users y seed"
            ))
            return

        agentes = [agente_karina, agente_isabel]

        for i, (nombre, telefono, email, origen, etapa_nombre, valor, titulo, descripcion, dias) in enumerate(DATOS):
            lead, created = Lead.objects.get_or_create(
                telefono=telefono,
                defaults={
                    "nombre_contacto": nombre,
                    "email": email,
                    "origen": origen,
                    "agente_asignado": agentes[i % 2],
                },
            )

            # Vincular Lead a un Cliente (requerido por Cotizacion).
            # get_or_create por teléfono para que sea idempotente.
            if not lead.cliente:
                cliente, _ = Cliente.objects.get_or_create(
                    telefono=telefono,
                    defaults={
                        "nombre": nombre,
                        "tipo_entidad": Cliente.TipoEntidad.NATURAL,
                        "segmento": Cliente.Segmento.MOSTRADOR,
                        "etapa_ciclo": Cliente.EtapaCiclo.LEAD,
                        "creado_por": admin,
                    },
                )
                lead.cliente = cliente
                lead.save(update_fields=["cliente"])

            self.stdout.write(f"  {'[+]' if created else '[ ]'} Lead: {lead.nombre_contacto}")

            if etapa_nombre is None:
                continue

            etapa_obj = _etapa(pipeline, etapa_nombre)
            es_cierre = etapa_obj.tipo in (Etapa.Tipo.GANADA, Etapa.Tipo.PERDIDA)

            oportunidad, op_created = Oportunidad.objects.get_or_create(
                lead=lead,
                pipeline=pipeline,
                defaults={
                    "etapa_actual": etapa_obj,
                    "titulo": titulo,
                    "valor_estimado": valor,
                    "descripcion": descripcion,
                    "motivo_perdida": MOTIVOS_PERDIDA.get(etapa_nombre, ""),
                    "fecha_cierre_estimada": (timezone.now() + timedelta(days=14)).date(),
                    "fecha_cierre_real": timezone.now() - timedelta(days=dias) if es_cierre else None,
                    "creado_por": admin,
                },
            )

            if op_created:
                _registrar_progreso(oportunidad, etapa_obj, agentes[i % 2], dias)
                self.stdout.write(
                    f"       → Oportunidad: {oportunidad.titulo or oportunidad} [{etapa_nombre}]"
                )

        self.stdout.write(self.style.SUCCESS("\nSeed de oportunidades completado."))
