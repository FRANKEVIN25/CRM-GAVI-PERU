from django.core.exceptions import ValidationError

from oportunidades.models import Actividad

from .models import Tarea

# Tipos de Tarea que generan una Actividad en el timeline al completarse.
# llamada → Actividad LLAMADA (registro directo de la llamada realizada)
# correo  → Actividad NOTA    (el correo se deja como nota en el historial)
# reunion → Actividad NOTA    (la reunión se resume como nota)
# otro    → sin Actividad automática
_TIPO_A_ACTIVIDAD: dict[str, str | None] = {
    Tarea.Tipo.LLAMADA: Actividad.Tipo.LLAMADA,
    Tarea.Tipo.CORREO: Actividad.Tipo.NOTA,
    Tarea.Tipo.REUNION: Actividad.Tipo.NOTA,
    Tarea.Tipo.OTRO: None,
}


def completar_tarea(tarea: Tarea, agente=None) -> Tarea:
    """
    Marca la tarea como COMPLETADA y, si el tipo tiene mapeo directo,
    crea una Actividad en el timeline del mismo objeto (Lead u Oportunidad).

    Nunca se llama desde save(). Usar siempre este servicio para completar.
    """
    if tarea.estado == Tarea.Estado.COMPLETADA:
        raise ValidationError("Esta tarea ya está completada.")

    tarea.estado = Tarea.Estado.COMPLETADA
    tarea.save(update_fields=["estado", "actualizado"])

    tipo_actividad = _TIPO_A_ACTIVIDAD.get(tarea.tipo)
    if tipo_actividad:
        Actividad.objects.create(
            content_type=tarea.content_type,
            object_id=tarea.object_id,
            tipo=tipo_actividad,
            agente=agente or tarea.asignada_a,
            descripcion=tarea.notas or tarea.titulo,
        )

    return tarea
