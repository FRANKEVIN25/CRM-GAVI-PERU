import json

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def conversaciones_data_script(conversaciones):
    data = []
    for conversacion in conversaciones:
        data.append({
            "id": conversacion.id,
            "sede": conversacion.sede.nombre,
            "sede_id": conversacion.sede_id,
            "nombre": conversacion.nombre_contacto or (conversacion.cliente.nombre if conversacion.cliente else "Nuevo contacto"),
            "telefono": conversacion.telefono,
            "estado": conversacion.estado,
            "cliente": conversacion.cliente_id,
            "cotizacion": conversacion.cotizacion_id,
            "abrir_url": reverse("cotizaciones:abrir_conversacion", args=[conversacion.id]),
            "enviar_url": reverse("cotizaciones:enviar_mensaje_whatsapp", args=[conversacion.id]),
            "mensajes": [{
                "id": mensaje.id,
                "direccion": mensaje.direccion,
                "contenido": mensaje.contenido,
                "leido": mensaje.leido,
                "creado": mensaje.creado.isoformat(),
            } for mensaje in conversacion.mensajes.all()],
        })
    return mark_safe('<script type="application/json" id="conversaciones-data">%s</script>' % json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
