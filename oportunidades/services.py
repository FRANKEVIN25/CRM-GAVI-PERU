from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import CambioEtapa, Etapa, Lead, Oportunidad, Pipeline


def _agente_from_usuario(usuario):
    """Resuelve el Agente a partir de un Usuario (puede ser None)."""
    if usuario is None:
        return None
    try:
        return usuario.agente
    except Exception:
        return None


def crear_oportunidad(*, lead=None, cliente=None, usuario=None, titulo="", etapa=None):
    """
    Crea una Oportunidad en la primera etapa operativa del pipeline activo.
    Acepta `lead` directamente o `cliente` (crea un Lead implícito vinculado al cliente).
    """
    with transaction.atomic():
        if lead is None and cliente is not None:
            lead = Lead.objects.create(
                nombre_contacto=cliente.nombre,
                telefono=cliente.telefono,
                cliente=cliente,
                origen=Lead.Origen.MANUAL,
            )
        if lead is None:
            raise ValidationError("Se requiere un lead o un cliente para crear la oportunidad.")
        if etapa is None:
            pipeline = Pipeline.objects.select_for_update().filter(activo=True).order_by("id").first()
            if not pipeline:
                raise ValidationError("No existe un pipeline activo para crear la oportunidad.")
            etapa = pipeline.etapas.filter(tipo=Etapa.Tipo.EN_PROGRESO).order_by("orden").first()
        if etapa is None or etapa.tipo != Etapa.Tipo.EN_PROGRESO:
            raise ValidationError("La oportunidad debe iniciar en una etapa en progreso.")
        oportunidad = Oportunidad.objects.create(
            lead=lead, pipeline=etapa.pipeline, etapa_actual=etapa,
            titulo=titulo, creado_por=usuario,
        )
        CambioEtapa.objects.create(
            oportunidad=oportunidad, etapa_nueva=etapa,
            agente=_agente_from_usuario(usuario),
        )
        return oportunidad


def mover_oportunidad_de_etapa(*, oportunidad_id, etapa_nueva, usuario=None):
    """Mueve etapas operativas; los cierres usan servicios explícitos separados."""
    with transaction.atomic():
        oportunidad = Oportunidad.objects.select_for_update().select_related(
            "etapa_actual", "pipeline"
        ).get(pk=oportunidad_id)
        if oportunidad.esta_cerrada:
            raise ValidationError("Una oportunidad cerrada no puede moverse de etapa.")
        if etapa_nueva.pipeline_id != oportunidad.pipeline_id:
            raise ValidationError("La etapa elegida pertenece a otro pipeline.")
        if etapa_nueva.tipo != Etapa.Tipo.EN_PROGRESO:
            raise ValidationError("Usa el servicio de cierre para etapas ganadas o perdidas.")
        anterior = oportunidad.etapa_actual
        if anterior.pk == etapa_nueva.pk:
            return oportunidad
        oportunidad.etapa_actual = etapa_nueva
        oportunidad.save(update_fields=["etapa_actual", "actualizado"])
        CambioEtapa.objects.create(
            oportunidad=oportunidad, etapa_anterior=anterior, etapa_nueva=etapa_nueva,
            agente=_agente_from_usuario(usuario),
        )
        return oportunidad


def _cerrar_oportunidad(*, oportunidad_id, etapa_cierre, usuario=None, motivo_perdida=""):
    with transaction.atomic():
        oportunidad = Oportunidad.objects.select_for_update().select_related(
            "etapa_actual", "pipeline"
        ).get(pk=oportunidad_id)
        if oportunidad.esta_cerrada:
            raise ValidationError("La oportunidad ya está cerrada.")
        if etapa_cierre.pipeline_id != oportunidad.pipeline_id:
            raise ValidationError("La etapa de cierre pertenece a otro pipeline.")
        if etapa_cierre.tipo not in (Etapa.Tipo.GANADA, Etapa.Tipo.PERDIDA):
            raise ValidationError("La etapa elegida no es una etapa de cierre.")
        anterior = oportunidad.etapa_actual
        oportunidad.etapa_actual = etapa_cierre
        oportunidad.fecha_cierre_real = timezone.now()
        oportunidad.motivo_perdida = motivo_perdida if etapa_cierre.tipo == Etapa.Tipo.PERDIDA else ""
        oportunidad.save(update_fields=["etapa_actual", "fecha_cierre_real", "motivo_perdida", "actualizado"])
        CambioEtapa.objects.create(
            oportunidad=oportunidad, etapa_anterior=anterior, etapa_nueva=etapa_cierre,
            agente=_agente_from_usuario(usuario),
        )
        return oportunidad


def cerrar_oportunidad_ganada(*, oportunidad_id, etapa_ganada, usuario=None):
    """Cierra una venta junto con su única cotización vigente confirmada."""
    from cotizaciones.models import Cotizacion
    from cotizaciones.services import transicionar_cotizacion

    with transaction.atomic():
        oportunidad = Oportunidad.objects.select_for_update().get(pk=oportunidad_id)
        cotizacion = Cotizacion.objects.select_for_update().filter(
            oportunidad=oportunidad, vigente=True
        ).first()
        if not cotizacion:
            raise ValidationError("No se puede ganar una oportunidad sin una cotización vigente.")
        if cotizacion.estado != Cotizacion.Estado.CONFIRMADA:
            raise ValidationError("La cotización vigente debe estar confirmada para cerrar la venta.")
        transicionar_cotizacion(cotizacion_id=cotizacion.pk, nuevo_estado=Cotizacion.Estado.CONVERTIDA)
        return _cerrar_oportunidad(
            oportunidad_id=oportunidad.pk, etapa_cierre=etapa_ganada, usuario=usuario,
        )


def cerrar_oportunidad_perdida(*, oportunidad_id, etapa_perdida, usuario=None, motivo_perdida=""):
    return _cerrar_oportunidad(
        oportunidad_id=oportunidad_id, etapa_cierre=etapa_perdida,
        usuario=usuario, motivo_perdida=motivo_perdida,
    )

    """Crea un trato en la primera etapa operativa, sin exigir una cotización."""
    with transaction.atomic():
        if etapa is None:
            pipeline = Pipeline.objects.select_for_update().filter(activo=True).order_by("id").first()
            if not pipeline:
                raise ValidationError("No existe un pipeline activo para crear la oportunidad.")
            etapa = pipeline.etapas.filter(tipo=Etapa.Tipo.EN_PROGRESO).order_by("orden").first()
        if etapa is None or etapa.tipo != Etapa.Tipo.EN_PROGRESO:
            raise ValidationError("La oportunidad debe iniciar en una etapa en progreso.")
        oportunidad = Oportunidad.objects.create(
            cliente=cliente, pipeline=etapa.pipeline, etapa=etapa, titulo=titulo, creado_por=usuario,
        )
        CambioEtapa.objects.create(oportunidad=oportunidad, etapa_nueva=etapa, agente=None)
        return oportunidad


def mover_oportunidad_de_etapa(*, oportunidad_id, etapa_nueva, usuario=None):
    """Mueve etapas operativas; los cierres usan servicios explícitos separados."""
    with transaction.atomic():
        oportunidad = Oportunidad.objects.select_for_update().select_related("etapa_actual", "pipeline").get(pk=oportunidad_id)
        if oportunidad.esta_cerrada:
            raise ValidationError("Una oportunidad cerrada no puede moverse de etapa.")
        if etapa_nueva.pipeline_id != oportunidad.pipeline_id:
            raise ValidationError("La etapa elegida pertenece a otro pipeline.")
        if etapa_nueva.tipo != Etapa.Tipo.EN_PROGRESO:
            raise ValidationError("Usa el servicio de cierre para etapas ganadas o perdidas.")
        anterior = oportunidad.etapa_actual
        if anterior.pk == etapa_nueva.pk:
            return oportunidad
        oportunidad.etapa_actual = etapa_nueva
        oportunidad.save(update_fields=["etapa_actual", "actualizado"])
        CambioEtapa.objects.create(
            oportunidad=oportunidad, etapa_anterior=anterior, etapa_nueva=etapa_nueva, agente=None,
        )
        return oportunidad


def _cerrar_oportunidad(*, oportunidad_id, etapa_cierre, usuario=None, motivo_perdida=""):
    with transaction.atomic():
        oportunidad = Oportunidad.objects.select_for_update().select_related("etapa_actual", "pipeline").get(pk=oportunidad_id)
        if oportunidad.esta_cerrada:
            raise ValidationError("La oportunidad ya está cerrada.")
        if etapa_cierre.pipeline_id != oportunidad.pipeline_id:
            raise ValidationError("La etapa de cierre pertenece a otro pipeline.")
        if etapa_cierre.tipo not in (Etapa.Tipo.GANADA, Etapa.Tipo.PERDIDA):
            raise ValidationError("La etapa elegida no es una etapa de cierre.")
        anterior = oportunidad.etapa_actual
        oportunidad.etapa_actual = etapa_cierre
        oportunidad.fecha_cierre_real = timezone.now()
        oportunidad.motivo_perdida = motivo_perdida if etapa_cierre.tipo == Etapa.Tipo.PERDIDA else ""
        oportunidad.save(update_fields=["etapa_actual", "fecha_cierre_real", "motivo_perdida", "actualizado"])
        CambioEtapa.objects.create(oportunidad=oportunidad, etapa_anterior=anterior, etapa_nueva=etapa_cierre, agente=None)
        return oportunidad


def cerrar_oportunidad_ganada(*, oportunidad_id, etapa_ganada, usuario=None):
    """Cierra una venta junto con su única cotización vigente confirmada."""
    from cotizaciones.models import Cotizacion
    from cotizaciones.services import transicionar_cotizacion

    with transaction.atomic():
        oportunidad = Oportunidad.objects.select_for_update().get(pk=oportunidad_id)
        cotizacion = Cotizacion.objects.select_for_update().filter(
            oportunidad=oportunidad, vigente=True
        ).first()
        if not cotizacion:
            raise ValidationError("No se puede ganar una oportunidad sin una cotización vigente.")
        if cotizacion.estado != Cotizacion.Estado.CONFIRMADA:
            raise ValidationError("La cotización vigente debe estar confirmada para cerrar la venta.")
        transicionar_cotizacion(cotizacion_id=cotizacion.pk, nuevo_estado=Cotizacion.Estado.CONVERTIDA)
        return _cerrar_oportunidad(
            oportunidad_id=oportunidad.pk, etapa_cierre=etapa_ganada, usuario=usuario,
        )


def cerrar_oportunidad_perdida(*, oportunidad_id, etapa_perdida, usuario=None, motivo_perdida=""):
    """Cierra sin tocar ofertas históricas; actualiza la vigente si corresponde."""
    from cotizaciones.models import Cotizacion
    from cotizaciones.services import transicionar_cotizacion

    with transaction.atomic():
        oportunidad = Oportunidad.objects.select_for_update().get(pk=oportunidad_id)
        cotizacion = Cotizacion.objects.select_for_update().filter(
            oportunidad=oportunidad, vigente=True
        ).first()
        if cotizacion and cotizacion.estado != Cotizacion.Estado.PERDIDA:
            if not cotizacion.puede_transicionar_a(Cotizacion.Estado.PERDIDA):
                raise ValidationError("La cotización vigente no puede marcarse como perdida desde su estado actual.")
            transicionar_cotizacion(cotizacion_id=cotizacion.pk, nuevo_estado=Cotizacion.Estado.PERDIDA)
        return _cerrar_oportunidad(
            oportunidad_id=oportunidad.pk, etapa_cierre=etapa_perdida, usuario=usuario, motivo_perdida=motivo_perdida,
        )
