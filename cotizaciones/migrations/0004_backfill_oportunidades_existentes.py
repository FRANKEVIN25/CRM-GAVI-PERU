from django.db import migrations


def crear_oportunidades_existentes(apps, schema_editor):
    Cotizacion = apps.get_model("cotizaciones", "Cotizacion")
    Pipeline = apps.get_model("oportunidades", "Pipeline")
    Etapa = apps.get_model("oportunidades", "Etapa")
    Oportunidad = apps.get_model("oportunidades", "Oportunidad")
    CambioEtapa = apps.get_model("oportunidades", "CambioEtapa")

    pipeline = Pipeline.objects.filter(nombre="Venta de repuestos").first()
    if not pipeline:
        return
    nombres_etapa = {
        "ENVIADA": "Cotización enviada",
        "CONFIRMADA": "Cotización confirmada",
        "CONVERTIDA": "Venta ganada",
        "PERDIDA": "Venta perdida",
    }
    etapas = {etapa.nombre: etapa for etapa in Etapa.objects.filter(pipeline=pipeline)}
    for cotizacion in Cotizacion.objects.filter(oportunidad__isnull=True).iterator():
        etapa = etapas[nombres_etapa[cotizacion.estado]]
        cerrada_en = cotizacion.actualizado if etapa.tipo in ("GANADA", "PERDIDA") else None
        oportunidad = Oportunidad.objects.create(
            cliente_id=cotizacion.cliente_id,
            pipeline_id=pipeline.pk,
            etapa_id=etapa.pk,
            creado_por_id=cotizacion.usuario_id,
            titulo=cotizacion.descripcion_repuesto[:150],
            cerrada_en=cerrada_en,
        )
        Oportunidad.objects.filter(pk=oportunidad.pk).update(creado=cotizacion.fecha, actualizado=cotizacion.actualizado)
        cambio = CambioEtapa.objects.create(
            oportunidad_id=oportunidad.pk,
            etapa_nueva_id=etapa.pk,
            cambiado_por_id=cotizacion.usuario_id,
        )
        CambioEtapa.objects.filter(pk=cambio.pk).update(cambiado_en=cotizacion.fecha)
        Cotizacion.objects.filter(pk=cotizacion.pk).update(oportunidad_id=oportunidad.pk, vigente=True)


class Migration(migrations.Migration):
    dependencies = [("cotizaciones", "0003_cotizacion_oportunidad_y_vigencia")]

    # El backfill es conservador y no se revierte automáticamente: después de
    # producción podrían existir oportunidades nuevas indistinguibles de las
    # históricas. Un rollback de esquema no debe borrar datos comerciales.
    operations = [migrations.RunPython(crear_oportunidades_existentes, migrations.RunPython.noop)]
