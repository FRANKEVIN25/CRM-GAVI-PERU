from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Cotizacion


def transicionar_cotizacion(*, cotizacion_id, nuevo_estado):
    """Única puerta operacional para cambiar el estado de una cotización."""
    with transaction.atomic():
        cotizacion = Cotizacion.objects.select_for_update().get(pk=cotizacion_id)
        if not cotizacion.puede_transicionar_a(nuevo_estado):
            raise ValidationError("Transición de estado inválida.")
        cotizacion.estado = nuevo_estado
        cotizacion.save(update_fields=["estado", "actualizado"])
        return cotizacion


def reemplazar_cotizacion(*, cotizacion_actual_id, cotizacion_nueva_id):
    """Mantiene una sola oferta vigente por oportunidad y conserva la cadena."""
    with transaction.atomic():
        actual = Cotizacion.objects.select_for_update().get(pk=cotizacion_actual_id)
        nueva = Cotizacion.objects.select_for_update().get(pk=cotizacion_nueva_id)
        if not actual.oportunidad_id or actual.oportunidad_id != nueva.oportunidad_id:
            raise ValidationError("Las cotizaciones deben pertenecer a la misma oportunidad.")
        if not actual.vigente:
            raise ValidationError("La cotización a reemplazar ya no está vigente.")
        actual.vigente = False
        actual.reemplazada_por = nueva
        actual.save(update_fields=["vigente", "reemplazada_por", "actualizado"])
        if not nueva.vigente:
            nueva.vigente = True
            nueva.save(update_fields=["vigente", "actualizado"])
        return nueva
