from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("oportunidades", "0001_initial"),
        ("cotizaciones", "0002_cotizacion_actualizado"),
    ]

    operations = [
        migrations.AddField(model_name="cotizacion", name="oportunidad", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cotizaciones", to="oportunidades.oportunidad")),
        migrations.AddField(model_name="cotizacion", name="vigente", field=models.BooleanField(default=True)),
        migrations.AddField(model_name="cotizacion", name="reemplazada_por", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reemplaza_a", to="cotizaciones.cotizacion")),
        migrations.AddConstraint(model_name="cotizacion", constraint=models.CheckConstraint(condition=models.Q(("descuento_pct__gte", 0), ("descuento_pct__lte", 100)), name="cotizacion_descuento_pct_entre_0_y_100")),
        migrations.AddConstraint(model_name="cotizacion", constraint=models.UniqueConstraint(condition=models.Q(("vigente", True), ("oportunidad__isnull", False)), fields=("oportunidad",), name="una_cotizacion_vigente_por_oportunidad")),
        migrations.AddIndex(model_name="cotizacion", index=models.Index(fields=["usuario", "estado"], name="cot_usuario_estado_idx")),
    ]
