import hashlib
import json
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone

from clientes.models import Cliente
from clientes.telefonos import normalizar_e164

from .models import AdjuntoWhatsApp, Conversacion, EventoWebhookWhatsApp, MensajeWhatsApp, NumeroWhatsApp


def _sin_prefijo_whatsapp(valor):
    return valor.removeprefix("whatsapp:").strip()


def _registrar_evento(payload, numero=None):
    serializado = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload_hash = hashlib.sha256(serializado.encode()).hexdigest()
    try:
        # Savepoint propio: una entrega duplicada no debe romper la transaccion
        # exterior que consulta el evento ya existente.
        with transaction.atomic():
            evento = EventoWebhookWhatsApp.objects.create(
                numero=numero, proveedor=NumeroWhatsApp.Proveedor.TWILIO,
                evento_id_proveedor=payload.get("MessageSid", ""), payload_hash=payload_hash, payload=payload,
            )
        return evento, True
    except IntegrityError:
        return EventoWebhookWhatsApp.objects.get(payload_hash=payload_hash), False


@transaction.atomic
def recibir_mensaje_twilio(payload):
    destino = normalizar_e164(_sin_prefijo_whatsapp(payload.get("To", "")))
    origen = normalizar_e164(_sin_prefijo_whatsapp(payload.get("From", "")))
    numero = NumeroWhatsApp.objects.filter(
        telefono=destino, proveedor=NumeroWhatsApp.Proveedor.TWILIO, activo=True,
    ).select_related("sede").first()
    if not numero or not origen:
        raise ValueError("El webhook no corresponde a un numero Twilio activo del CRM.")

    evento, nuevo = _registrar_evento(payload, numero)
    if not nuevo or evento.procesado:
        return None
    try:
        cliente = Cliente.objects.filter(telefono_normalizado=origen).first()
        conversacion, _ = Conversacion.objects.get_or_create(
            sede=numero.sede, telefono=origen,
            defaults={"numero": numero, "cliente": cliente, "nombre_contacto": payload.get("ProfileName", "")},
        )
        cambios = []
        if conversacion.numero_id is None:
            conversacion.numero = numero
            cambios.append("numero")
        if not conversacion.cliente_id and cliente:
            conversacion.cliente = cliente
            cambios.append("cliente")
        if payload.get("ProfileName") and not conversacion.nombre_contacto:
            conversacion.nombre_contacto = payload["ProfileName"]
            cambios.append("nombre_contacto")
        conversacion.ventana_expira_en = timezone.now() + timedelta(hours=24)
        cambios.extend(["ventana_expira_en", "actualizado"])
        conversacion.save(update_fields=cambios)

        mensaje, _ = MensajeWhatsApp.objects.get_or_create(
            conversacion=conversacion, proveedor_message_id=payload.get("MessageSid", ""),
            defaults={"direccion": MensajeWhatsApp.Direccion.ENTRANTE, "contenido": payload.get("Body", ""), "leido": False},
        )
        for indice in range(int(payload.get("NumMedia", "0") or 0)):
            AdjuntoWhatsApp.objects.get_or_create(
                mensaje=mensaje, proveedor_media_id=f'{payload.get("MessageSid", "")}:{indice}',
                defaults={"url_temporal": payload.get(f"MediaUrl{indice}", ""), "mime_type": payload.get(f"MediaContentType{indice}", "")},
            )
        evento.procesado = True
        evento.save(update_fields=["procesado"])
        return mensaje
    except Exception as error:
        evento.error = str(error)
        evento.save(update_fields=["error"])
        raise


ESTADOS_TWILIO = {
    "queued": MensajeWhatsApp.EstadoEntrega.ENVIADO,
    "sent": MensajeWhatsApp.EstadoEntrega.ENVIADO,
    "delivered": MensajeWhatsApp.EstadoEntrega.ENTREGADO,
    "read": MensajeWhatsApp.EstadoEntrega.LEIDO,
    "failed": MensajeWhatsApp.EstadoEntrega.FALLIDO,
    "undelivered": MensajeWhatsApp.EstadoEntrega.FALLIDO,
}


@transaction.atomic
def actualizar_estado_twilio(payload):
    evento, nuevo = _registrar_evento(payload)
    if not nuevo or evento.procesado:
        return None
    mensaje = MensajeWhatsApp.objects.filter(proveedor_message_id=payload.get("MessageSid", "")).first()
    if mensaje and payload.get("MessageStatus") in ESTADOS_TWILIO:
        mensaje.estado_entrega = ESTADOS_TWILIO[payload["MessageStatus"]]
        mensaje.save(update_fields=["estado_entrega"])
    evento.procesado = True
    evento.save(update_fields=["procesado"])
    return mensaje
