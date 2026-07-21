import json

from django import template
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def cotizaciones_data_script(queryset):
    """
    Serializa las cotizaciones (ya filtradas por la vista) a JSON para que
    CotizacionesList.svelte las hidrate sin pedirlas de nuevo al servidor.
    Incluye los estados siguientes validos para que el cambio de estado en
    el cliente respete la misma maquina de estados que la vista.
    """
    data = [
        {
            'id': c.id,
            'cliente': str(c.cliente),
            'usuario': str(c.usuario),
            'descripcion_repuesto': c.descripcion_repuesto,
            'codigo_producto': c.codigo_producto,
            'descuento_pct': str(c.descuento_pct),
            'estado': c.estado,
            'estado_display': c.get_estado_display(),
            'siguientes_estados': [
                {'value': e.value, 'label': e.label} for e in c.siguientes_estados()
            ],
            'fecha': c.fecha.strftime('%d/%m/%Y %H:%M'),
            'update_url': reverse('cotizaciones:update_estado', args=[c.id]),
        }
        for c in queryset
    ]
    json_str = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return mark_safe(
        f'<script type="application/json" id="cotizaciones-data">{json_str}</script>'
    )


@register.simple_tag
def tablero_data_script(queryset):
    """
    Serializa el tablero Kanban del vendedor (siempre sus propias
    cotizaciones -- lo filtra la vista, no este tag). `dias_desde_actualizacion`
    usa el campo `actualizado` (auto_now), no `fecha` (creacion), para que
    una cotizacion vieja que recien cambio de estado no se vea como
    estancada. `cliente_telefono` va aparte para que el frontend intente
    cruzarlo con la conversacion mock de WhatsApp -- ese cruce es puramente
    de UI, no vive en el modelo.
    """
    ahora = timezone.now()
    data = [
        {
            'id': c.id,
            'cliente': str(c.cliente),
            'cliente_telefono': c.cliente.telefono,
            'descripcion_repuesto': c.descripcion_repuesto,
            'codigo_producto': c.codigo_producto,
            'estado': c.estado,
            'estado_display': c.get_estado_display(),
            'dias_desde_actualizacion': (ahora - c.actualizado).days,
            'update_url': reverse('cotizaciones:update_estado', args=[c.id]),
        }
        for c in queryset
    ]
    json_str = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return mark_safe(
        f'<script type="application/json" id="tablero-data">{json_str}</script>'
    )


@register.simple_tag
def oportunidades_data_script(queryset):
    """Datos del pipeline real: una tarjeta representa una oportunidad, no un mock."""
    ahora = timezone.now()
    data = []
    for oportunidad in queryset:
        cotizacion = next((c for c in oportunidad.cotizaciones.all() if c.vigente), None)
        data.append({
            "id": oportunidad.id,
            "cliente": oportunidad.cliente.nombre,
            "titulo": oportunidad.titulo,
            "etapa_id": oportunidad.etapa_id,
            "dias_desde_actualizacion": (ahora - oportunidad.actualizado).days,
            "cotizacion": {
                "id": cotizacion.id,
                "descripcion": cotizacion.descripcion_repuesto,
                "estado": cotizacion.estado,
            } if cotizacion else None,
            "update_url": reverse("cotizaciones:mover_oportunidad", args=[oportunidad.id]),
        })
    json_str = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return mark_safe(f'<script type="application/json" id="oportunidades-data">{json_str}</script>')


@register.simple_tag
def etapas_data_script(queryset):
    data = [
        {"id": etapa.id, "nombre": etapa.nombre, "tipo": etapa.tipo, "pipeline": etapa.pipeline.nombre}
        for etapa in queryset
    ]
    json_str = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return mark_safe(f'<script type="application/json" id="etapas-data">{json_str}</script>')


@register.simple_tag
def clientes_data_script(queryset):
    """
    Lista de clientes para el <select> del mini-formulario "crear
    cotización" que aparece en la columna "Mensajes nuevos" del tablero.
    Solo id/nombre/telefono -- lo mismo que ya usa CotizacionForm.cliente,
    serializado para poder renderizarlo desde Svelte.
    """
    data = [
        {'id': c.id, 'nombre': c.nombre, 'telefono': c.telefono}
        for c in queryset
    ]
    json_str = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return mark_safe(
        f'<script type="application/json" id="clientes-data">{json_str}</script>'
    )
