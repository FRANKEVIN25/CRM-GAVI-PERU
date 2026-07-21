import phonenumbers
from django.db import migrations, models


def normalizar_telefonos_existentes(apps, schema_editor):
    Cliente = apps.get_model("clientes", "Cliente")
    for cliente in Cliente.objects.all().only("id", "telefono").iterator():
        try:
            numero = phonenumbers.parse(cliente.telefono, "PE")
            normalizado = phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164) if phonenumbers.is_valid_number(numero) else None
        except phonenumbers.NumberParseException:
            normalizado = None
        Cliente.objects.filter(pk=cliente.pk).update(telefono_normalizado=normalizado)


class Migration(migrations.Migration):
    dependencies = [("clientes", "0003_alter_cliente_segmento")]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="telefono_normalizado",
            field=models.CharField(blank=True, db_index=True, max_length=16, null=True),
        ),
        migrations.RunPython(normalizar_telefonos_existentes, migrations.RunPython.noop),
    ]
