"""Adaptador de Twilio. Ninguna regla de negocio debe depender de su SDK."""

from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse


@dataclass(frozen=True)
class ResultadoEnvio:
    message_id: str
    estado: str


def esta_configurado():
    return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)


def validar_firma(*, url, parametros, firma):
    if not settings.TWILIO_AUTH_TOKEN:
        return False
    from twilio.request_validator import RequestValidator

    return RequestValidator(settings.TWILIO_AUTH_TOKEN).validate(url, parametros, firma)


def enviar_texto(*, desde, hacia, contenido):
    if not esta_configurado():
        raise ImproperlyConfigured("Twilio todavia no esta configurado.")
    from twilio.rest import Client

    callback = None
    if settings.TWILIO_WEBHOOK_BASE_URL:
        callback = settings.TWILIO_WEBHOOK_BASE_URL + reverse("whatsapp:twilio_estado")
    opciones = {
        "from_": f"whatsapp:{desde}",
        "to": f"whatsapp:{hacia}",
        "body": contenido,
    }
    if callback:
        opciones["status_callback"] = callback
    respuesta = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN).messages.create(**opciones)
    return ResultadoEnvio(message_id=respuesta.sid, estado=respuesta.status)
