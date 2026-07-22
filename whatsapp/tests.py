from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import AdjuntoWhatsApp, Conversacion, EventoWebhookWhatsApp, MensajeWhatsApp, NumeroWhatsApp, Sede
from .services import actualizar_estado_twilio, recibir_mensaje_twilio


class WhatsappSinPaginaPropiaTests(TestCase):
    """
    La interfaz de WhatsApp se consolidó dentro de /cotizaciones/tablero/
    (columna "Mensajes nuevos" + ChatFlotante). Esta app ya no expone
    ninguna vista ni ruta propia -- solo sirve como contenedor de los
    estáticos que reutiliza ChatFlotante.svelte.
    """

    def test_no_existe_una_pagina_separada_de_whatsapp(self):
        response = self.client.get("/whatsapp/", secure=True)
        self.assertEqual(response.status_code, 404)


class WhatsappModelsTests(TestCase):
    def setUp(self):
        self.sede = Sede.objects.create(nombre="México", telefono_whatsapp="999111222")

    def test_numero_normaliza_a_e164_y_protege_identidad_del_proveedor(self):
        numero = NumeroWhatsApp.objects.create(
            sede=self.sede, telefono="999 111 222", proveedor=NumeroWhatsApp.Proveedor.TWILIO,
            proveedor_numero_id="PN123",
        )

        self.assertEqual(numero.telefono, "+51999111222")
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                NumeroWhatsApp.objects.create(
                    sede=self.sede, telefono="999222333", proveedor=NumeroWhatsApp.Proveedor.TWILIO,
                    proveedor_numero_id="PN123",
                )

    def test_mensaje_externo_es_idempotente_por_conversacion(self):
        numero = NumeroWhatsApp.objects.create(sede=self.sede, telefono="999111222")
        conversacion = Conversacion.objects.create(sede=self.sede, numero=numero, telefono="999222333")
        MensajeWhatsApp.objects.create(
            conversacion=conversacion, direccion=MensajeWhatsApp.Direccion.ENTRANTE,
            contenido="Hola", proveedor_message_id="wamid.123",
        )

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                MensajeWhatsApp.objects.create(
                    conversacion=conversacion, direccion=MensajeWhatsApp.Direccion.ENTRANTE,
                    contenido="Hola otra vez", proveedor_message_id="wamid.123",
                )


class TwilioServicesTests(TestCase):
    def setUp(self):
        sede = Sede.objects.create(nombre="Lima")
        self.numero = NumeroWhatsApp.objects.create(
            sede=sede, telefono="999111222", proveedor=NumeroWhatsApp.Proveedor.TWILIO,
        )
        self.payload = {
            "MessageSid": "SM123", "From": "whatsapp:+51999222333",
            "To": f"whatsapp:{self.numero.telefono}", "Body": "Necesito una cotizacion",
            "ProfileName": "Rosa", "NumMedia": "1", "MediaUrl0": "https://api.twilio.test/media/1",
            "MediaContentType0": "image/jpeg",
        }

    def test_recibe_mensaje_con_adjunto_y_reintento_idempotente(self):
        mensaje = recibir_mensaje_twilio(self.payload)
        repetido = recibir_mensaje_twilio(self.payload)

        self.assertIsNone(repetido)
        self.assertEqual(mensaje.conversacion.nombre_contacto, "Rosa")
        self.assertEqual(AdjuntoWhatsApp.objects.count(), 1)
        self.assertEqual(EventoWebhookWhatsApp.objects.count(), 1)

    def test_actualiza_estado_de_entrega(self):
        mensaje = recibir_mensaje_twilio(self.payload)
        actualizar_estado_twilio({"MessageSid": "SM123", "MessageStatus": "read"})
        mensaje.refresh_from_db()
        self.assertEqual(mensaje.estado_entrega, MensajeWhatsApp.EstadoEntrega.LEIDO)


@override_settings(TWILIO_AUTH_TOKEN="token")
class TwilioWebhookTests(TestCase):
    def test_rechaza_webhook_sin_firma(self):
        response = self.client.post(reverse("whatsapp:twilio_entrante"), {}, secure=True)
        self.assertEqual(response.status_code, 403)
