from django.test import TestCase


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
