from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("oportunidades", "0001_initial"),
        ("seguimientos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="seguimiento", name="oportunidad",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="seguimientos", to="oportunidades.oportunidad"),
        ),
    ]
