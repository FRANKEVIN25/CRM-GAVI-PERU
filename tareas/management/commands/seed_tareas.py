"""
Seed de Tareas para el CRM GAVI PERU.
Uso: python manage.py seed_tareas

Prerequisitos:
  python manage.py seed_users
  python manage.py seed_pipeline
  python manage.py seed_oportunidades

Crea tareas en los tres estados (pendiente, completada, vencida) sobre
Leads y Oportunidades existentes, distribuidas entre Karina e Isabel.
"""

from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from oportunidades.models import Lead, Oportunidad
from tareas.models import Tarea
from usuarios.models import Agente


class Command(BaseCommand):
    help = "Carga tareas de desarrollo para GAVI PERU."

    def handle(self, *args, **options):
        try:
            karina = Agente.objects.get(usuario__username="karina_v")
            isabel = Agente.objects.get(usuario__username="isabel_r")
        except Agente.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                "Agentes no encontrados. Corre primero: seed_users"
            ))
            return

        ahora = timezone.now()
        ct_lead = ContentType.objects.get_for_model(Lead)
        ct_opp = ContentType.objects.get_for_model(Oportunidad)

        TAREAS = [
            # Tareas PENDIENTES sobre Leads
            {
                "ct": ct_lead, "telefono": "987001003",
                "titulo": "Llamar a Rosa — confirmar si tiene presupuesto esta semana",
                "tipo": Tarea.Tipo.LLAMADA, "prioridad": Tarea.Prioridad.ALTA,
                "notas": "Viene referida por Taller Norte. Primera compra.",
                "vencimiento": ahora + timedelta(hours=4),
                "asignada_a": isabel,
            },
            {
                "ct": ct_lead, "telefono": "987001007",
                "titulo": "Enviar catálogo de repuestos Chery por WhatsApp",
                "tipo": Tarea.Tipo.OTRO, "prioridad": Tarea.Prioridad.MEDIA,
                "notas": "Consultó repuestos varios. Enviar el PDF del catálogo vigente.",
                "vencimiento": ahora + timedelta(days=1),
                "asignada_a": karina,
            },
            {
                "ct": ct_lead, "telefono": "987001008",
                "titulo": "Calificar Taller Rímac — llamar para entender necesidad",
                "tipo": Tarea.Tipo.LLAMADA, "prioridad": Tarea.Prioridad.MEDIA,
                "notas": "Lead nuevo por referido. Aún no tenemos información del volumen.",
                "vencimiento": ahora + timedelta(days=2),
                "asignada_a": isabel,
            },
            # Tareas PENDIENTES sobre Oportunidades
            {
                "ct": ct_opp, "telefono": "987001001",
                "titulo": "Confirmar disponibilidad de frenos Chery Tiggo 4 con almacén",
                "tipo": Tarea.Tipo.LLAMADA, "prioridad": Tarea.Prioridad.ALTA,
                "notas": "El cliente dijo que el auto está inmovilizado. Prioridad máxima.",
                "vencimiento": ahora + timedelta(hours=2),
                "asignada_a": karina,
            },
            {
                "ct": ct_opp, "telefono": "987001002",
                "titulo": "Reunión con Taller San Borja — negociar descuento final",
                "tipo": Tarea.Tipo.REUNION, "prioridad": Tarea.Prioridad.ALTA,
                "notas": "Piden 5% adicional. Gerente aprobó hasta 7% para este cliente.",
                "vencimiento": ahora + timedelta(days=1),
                "asignada_a": isabel,
            },
            {
                "ct": ct_opp, "telefono": "987001010",
                "titulo": "Enviar pro-forma actualizada a Distribuidora Andina",
                "tipo": Tarea.Tipo.CORREO, "prioridad": Tarea.Prioridad.MEDIA,
                "notas": "Actualizar precios con la lista de julio 2026.",
                "vencimiento": ahora + timedelta(days=3),
                "asignada_a": karina,
            },
            # Tarea VENCIDA (simula un seguimiento olvidado)
            {
                "ct": ct_opp, "telefono": "987001004",
                "titulo": "Llamar al jefe de flota de Lima Express para calificar",
                "tipo": Tarea.Tipo.LLAMADA, "prioridad": Tarea.Prioridad.ALTA,
                "notas": "Contacto: Jorge Tarazona, +51 965432109.",
                "vencimiento": ahora - timedelta(days=2),  # ya venció
                "asignada_a": isabel,
            },
        ]

        for datos in TAREAS:
            # Resolver el object_id desde el Lead o Oportunidad
            try:
                lead = Lead.objects.get(telefono=datos["telefono"])
            except Lead.DoesNotExist:
                self.stdout.write(f"  [!] Lead {datos['telefono']} no encontrado, omitido.")
                continue

            if datos["ct"] == ct_opp:
                opp = lead.oportunidades.first()
                if not opp:
                    self.stdout.write(f"  [!] Sin oportunidad para {lead}, omitido.")
                    continue
                object_id = opp.pk
            else:
                object_id = lead.pk

            existente = Tarea.objects.filter(
                content_type=datos["ct"],
                object_id=object_id,
                titulo=datos["titulo"],
            ).exists()

            if existente:
                self.stdout.write(f"  [ ] Tarea ya existe: {datos['titulo'][:50]}")
                continue

            estado = Tarea.Estado.PENDIENTE
            if datos["vencimiento"] < timezone.now():
                estado = Tarea.Estado.VENCIDA

            tarea = Tarea.objects.create(
                content_type=datos["ct"],
                object_id=object_id,
                titulo=datos["titulo"],
                tipo=datos["tipo"],
                prioridad=datos["prioridad"],
                notas=datos["notas"],
                fecha_vencimiento=datos["vencimiento"],
                asignada_a=datos["asignada_a"],
                creada_por=datos["asignada_a"],
                estado=estado,
            )
            self.stdout.write(
                f"  [+] Tarea [{tarea.get_estado_display()}]: {tarea.titulo[:55]}"
            )

        self.stdout.write(self.style.SUCCESS("\nSeed de tareas completado."))
