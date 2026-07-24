"""
Seed del pipeline de ventas para el CRM GAVI PERU.
Uso: python manage.py seed_pipeline

Crea el pipeline estándar de GAVI con las etapas acordadas con el equipo
comercial, alineadas con las de HubSpot que ya conocen.

IMPORTANTE — leer antes de modificar:
  Las etapas son datos de configuración de negocio, no datos de prueba.
  Una vez que hay Oportunidades apuntando a una Etapa, eliminarla falla
  con un error de base de datos (on_delete=PROTECT). Esto es intencional.

  Regla práctica:
    ✓ Agregar una etapa nueva → siempre seguro
    ✓ Renombrar una etapa existente → seguro (solo cosmético)
    ✗ Eliminar una etapa con oportunidades → bloqueado por la BD
    ✗ Reordenar etapas con datos históricos → rompe métricas de embudo

  Si el proceso comercial cambia radicalmente, crear un pipeline nuevo
  y desactivar el anterior (Pipeline.activo=False). Las oportunidades
  históricas quedan intactas.

Etapas basadas en el pipeline de HubSpot ya configurado para GAVI:
  1. Prospección         → EN_PROGRESO
  2. Contacto Inicial    → EN_PROGRESO
  3. Calificación        → EN_PROGRESO
  4. Propuesta Enviada   → EN_PROGRESO
  5. Negociación         → EN_PROGRESO
  6. Cerrado Ganado      → GANADA
  7. Cerrado Perdido     → PERDIDA
"""

from django.core.management.base import BaseCommand

from oportunidades.models import Etapa, Pipeline

PIPELINE_NOMBRE = "Venta de Repuestos GAVI"

ETAPAS = [
    # (orden, nombre,              tipo,                    probabilidad_pct)
    (1, "Prospección",          Etapa.Tipo.EN_PROGRESO,  10),
    (2, "Contacto Inicial",     Etapa.Tipo.EN_PROGRESO,  20),
    (3, "Calificación",         Etapa.Tipo.EN_PROGRESO,  40),
    (4, "Propuesta Enviada",    Etapa.Tipo.EN_PROGRESO,  60),
    (5, "Negociación",          Etapa.Tipo.EN_PROGRESO,  80),
    (6, "Cerrado Ganado",       Etapa.Tipo.GANADA,       100),
    (7, "Cerrado Perdido",      Etapa.Tipo.PERDIDA,      0),
]


class Command(BaseCommand):
    help = "Crea el pipeline y etapas de ventas estándar de GAVI PERU."

    def handle(self, *args, **options):
        pipeline, created = Pipeline.objects.get_or_create(
            nombre=PIPELINE_NOMBRE,
            defaults={"activo": True},
        )
        self.stdout.write(
            f"  {'[+]' if created else '[ ]'} Pipeline: {pipeline.nombre}"
        )

        for orden, nombre, tipo, probabilidad in ETAPAS:
            etapa, created = Etapa.objects.get_or_create(
                pipeline=pipeline,
                orden=orden,
                defaults={"nombre": nombre, "tipo": tipo, "probabilidad_pct": probabilidad},
            )
            tipo_label = {"EN_PROGRESO": "→", "GANADA": "✓", "PERDIDA": "✗"}[tipo]
            self.stdout.write(
                f"  {'[+]' if created else '[ ]'} Etapa {orden}: {tipo_label} {etapa.nombre} ({etapa.probabilidad_pct}%)"
            )

        self.stdout.write(self.style.SUCCESS("\nPipeline configurado."))
        self.stdout.write(
            "  Para ver o ajustar etapas: /admin/oportunidades/pipeline/"
        )
