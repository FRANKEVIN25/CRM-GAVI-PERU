from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase

from .models import Conversacion, MensajeWhatsApp, NumeroWhatsApp, Sede


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
