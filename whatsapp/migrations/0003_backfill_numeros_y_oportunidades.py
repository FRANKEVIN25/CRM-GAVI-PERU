import phonenumbers
from django.db import migrations


def e164(valor):
    try:
        numero = phonenumbers.parse(valor, "PE")
        if phonenumbers.is_valid_number(numero):
            return phonenumbers.format_number(numero, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return None


def backfill_numeros_y_oportunidades(apps, schema_editor):
    Sede = apps.get_model("whatsapp", "Sede")
    NumeroWhatsApp = apps.get_model("whatsapp", "NumeroWhatsApp")
    Conversacion = apps.get_model("whatsapp", "Conversacion")
    Cotizacion = apps.get_model("cotizaciones", "Cotizacion")

    for sede in Sede.objects.exclude(telefono_whatsapp="").iterator():
        telefono = e164(sede.telefono_whatsapp)
        if not telefono:
            continue
        numero, _ = NumeroWhatsApp.objects.get_or_create(
            sede_id=sede.pk, telefono=telefono,
            defaults={"proveedor": "SIN_INTEGRAR", "activo": sede.activa},
        )
        Conversacion.objects.filter(sede_id=sede.pk, numero__isnull=True).update(numero_id=numero.pk)

    for conversacion in Conversacion.objects.exclude(cotizacion__isnull=True).filter(oportunidad_actual__isnull=True).iterator():
        oportunidad_id = Cotizacion.objects.filter(pk=conversacion.cotizacion_id).values_list("oportunidad_id", flat=True).first()
        if oportunidad_id:
            Conversacion.objects.filter(pk=conversacion.pk).update(oportunidad_actual_id=oportunidad_id)


class Migration(migrations.Migration):
    dependencies = [
        ("cotizaciones", "0004_backfill_oportunidades_existentes"),
        ("whatsapp", "0002_adjuntowhatsapp_eventowebhookwhatsapp_numerowhatsapp_and_more"),
    ]

    operations = [migrations.RunPython(backfill_numeros_y_oportunidades, migrations.RunPython.noop)]
