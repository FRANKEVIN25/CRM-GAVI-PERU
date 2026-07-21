from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def sembrar_pipeline_inicial(apps, schema_editor):
    Pipeline = apps.get_model("oportunidades", "Pipeline")
    Etapa = apps.get_model("oportunidades", "Etapa")
    pipeline, _ = Pipeline.objects.get_or_create(nombre="Venta de repuestos", defaults={"activo": True})
    etapas = [
        (10, "Nueva oportunidad", "EN_PROGRESO"),
        (20, "Cotización enviada", "EN_PROGRESO"),
        (30, "Cotización confirmada", "EN_PROGRESO"),
        (90, "Venta ganada", "GANADA"),
        (99, "Venta perdida", "PERDIDA"),
    ]
    for orden, nombre, tipo in etapas:
        Etapa.objects.get_or_create(pipeline=pipeline, orden=orden, defaults={"nombre": nombre, "tipo": tipo})


def deshacer_pipeline_inicial(apps, schema_editor):
    Pipeline = apps.get_model("oportunidades", "Pipeline")
    Pipeline.objects.filter(nombre="Venta de repuestos").delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("clientes", "0003_alter_cliente_segmento"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pipeline",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=100, unique=True)),
                ("activo", models.BooleanField(default=True)),
            ],
            options={"ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="Etapa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=60)),
                ("orden", models.PositiveSmallIntegerField()),
                ("tipo", models.CharField(choices=[("EN_PROGRESO", "En progreso"), ("GANADA", "Ganada"), ("PERDIDA", "Perdida")], default="EN_PROGRESO", max_length=16)),
                ("pipeline", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="etapas", to="oportunidades.pipeline")),
            ],
            options={"ordering": ["pipeline", "orden"]},
        ),
        migrations.CreateModel(
            name="Oportunidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(blank=True, max_length=150)),
                ("cerrada_en", models.DateTimeField(blank=True, null=True)),
                ("motivo_perdida", models.CharField(blank=True, max_length=255)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("cliente", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="oportunidades", to="clientes.cliente")),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="oportunidades_creadas", to=settings.AUTH_USER_MODEL)),
                ("etapa", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="oportunidades", to="oportunidades.etapa")),
                ("pipeline", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="oportunidades", to="oportunidades.pipeline")),
            ],
            options={"ordering": ["-actualizado"]},
        ),
        migrations.CreateModel(
            name="CambioEtapa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("cambiado_en", models.DateTimeField(auto_now_add=True)),
                ("cambiado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("etapa_anterior", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to="oportunidades.etapa")),
                ("etapa_nueva", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to="oportunidades.etapa")),
                ("oportunidad", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="historial_etapas", to="oportunidades.oportunidad")),
            ],
            options={"ordering": ["-cambiado_en"]},
        ),
        migrations.AddConstraint(model_name="etapa", constraint=models.UniqueConstraint(fields=("pipeline", "orden"), name="etapa_orden_unico_por_pipeline")),
        migrations.AddConstraint(model_name="etapa", constraint=models.UniqueConstraint(fields=("pipeline", "nombre"), name="etapa_nombre_unico_por_pipeline")),
        migrations.AddIndex(model_name="oportunidad", index=models.Index(fields=["cliente", "etapa"], name="oportunidad_cliente_etapa_idx")),
        migrations.AddIndex(model_name="cambioetapa", index=models.Index(fields=["oportunidad", "cambiado_en"], name="cambio_opp_fecha_idx")),
        migrations.RunPython(sembrar_pipeline_inicial, deshacer_pipeline_inicial),
    ]
