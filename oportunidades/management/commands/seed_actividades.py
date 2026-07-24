"""
Seed de Actividades para el CRM GAVI PERU.
Uso: python manage.py seed_actividades

Prerequisitos:
  python manage.py seed_users
  python manage.py seed_oportunidades

Crea un historial de actividades (notas, llamadas, mensajes WA) sobre
Leads y Oportunidades para poblar los timelines de la interfaz.
"""

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from oportunidades.models import Actividad, Lead, Oportunidad
from usuarios.models import Agente


class Command(BaseCommand):
    help = "Carga actividades (historial) de desarrollo para GAVI PERU."

    def handle(self, *args, **options):
        try:
            karina = Agente.objects.get(usuario__username="karina_v")
            isabel = Agente.objects.get(usuario__username="isabel_r")
        except Agente.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                "Agentes no encontrados. Corre primero: seed_users"
            ))
            return

        ct_lead = ContentType.objects.get_for_model(Lead)
        ct_opp = ContentType.objects.get_for_model(Oportunidad)

        # (telefono_lead, content_type, tipo, agente, descripcion)
        ACTIVIDADES = [
            # Lead Rosa Mamani — primeros contactos
            ("987001003", ct_lead, Actividad.Tipo.WHATSAPP, isabel,
             "Cliente escribió por WA: 'Buenas tardes, me recomendaron para filtros de mi Changan CS35'"),
            ("987001003", ct_lead, Actividad.Tipo.LLAMADA, isabel,
             "Llamé para calificar. Tiene presupuesto de S/450. Lleva el auto al taller el viernes."),

            # Oportunidad Taller San Borja — negociación activa
            ("987001002", ct_opp, Actividad.Tipo.LLAMADA, isabel,
             "Primera llamada con el encargado de compras. Confirman pedido mensual de ~3,500 soles."),
            ("987001002", ct_opp, Actividad.Tipo.NOTA, isabel,
             "El taller tiene 8 mecánicos. Trabajan principalmente con JAC S3 y Chery Tiggo. Potencial de crecer a cliente recurrente."),
            ("987001002", ct_opp, Actividad.Tipo.WHATSAPP, isabel,
             "Enviaron lista de repuestos por WA. La estoy cotizando con almacén."),

            # Oportunidad Pedro Quispe — ganada
            ("987001005", ct_opp, Actividad.Tipo.LLAMADA, karina,
             "Confirmó compra por teléfono. Pasa a recoger mañana a las 10am."),
            ("987001005", ct_opp, Actividad.Tipo.NOTA, karina,
             "Cotización CONVERTIDA. Pago al contado. Cliente satisfecho, dice que volverá."),

            # Oportunidad Importadora Del Norte — perdida
            ("987001006", ct_opp, Actividad.Tipo.LLAMADA, isabel,
             "Llamó para informar que encontraron proveedor directo en China con mejor precio."),
            ("987001006", ct_opp, Actividad.Tipo.NOTA, isabel,
             "Oportunidad perdida por precio. Revisar si podemos mejorar márgenes en repuestos motor Tiggo 7 para el próximo trimestre."),

            # Lead Ana Condori — prospección inicial
            ("987001007", ct_lead, Actividad.Tipo.WHATSAPP, karina,
             "Primer mensaje por WA: 'Hola, busco repuestos para mi Chery'. Respondí con catálogo."),

            # Oportunidad Flota Lima Express — en calificación
            ("987001004", ct_opp, Actividad.Tipo.NOTA, isabel,
             "RFQ recibido por el catálogo online. 12 vehículos JAC con mantenimiento vencido."),
            ("987001004", ct_opp, Actividad.Tipo.LLAMADA, isabel,
             "Hablé con la asistente. El jefe de flota (Jorge Tarazona) está de viaje hasta el lunes."),
        ]

        created_count = 0
        for telefono, ct, tipo, agente, descripcion in ACTIVIDADES:
            try:
                lead = Lead.objects.get(telefono=telefono)
            except Lead.DoesNotExist:
                self.stdout.write(f"  [!] Lead {telefono} no encontrado, omitido.")
                continue

            if ct == ct_opp:
                opp = lead.oportunidades.first()
                if not opp:
                    continue
                object_id = opp.pk
            else:
                object_id = lead.pk

            # Actividades son inmutables — no se crean duplicadas por descripción
            if Actividad.objects.filter(
                content_type=ct, object_id=object_id, descripcion=descripcion
            ).exists():
                continue

            Actividad.objects.create(
                content_type=ct,
                object_id=object_id,
                tipo=tipo,
                agente=agente,
                descripcion=descripcion,
            )
            created_count += 1
            tipo_label = {"nota": "📝", "llamada": "📞", "whatsapp": "💬"}[tipo]
            self.stdout.write(f"  [+] {tipo_label} {tipo:10} {descripcion[:60]}")

        self.stdout.write(self.style.SUCCESS(f"\nSeed de actividades completado. ({created_count} creadas)"))
