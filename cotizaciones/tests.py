from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from oportunidades.services import crear_oportunidad
from .models import Cotizacion


class CotizacionViewsTests(TestCase):
    def setUp(self):
        from oportunidades.models import Etapa, Pipeline
        User = get_user_model()
        self.vendedora1 = User.objects.create_user(username="vendedora1", password="clave123")
        self.vendedora2 = User.objects.create_user(username="vendedora2", password="clave123")
        self.cliente = Cliente.objects.create(nombre="Taller Norte", telefono="999111222")
        pipeline = Pipeline.objects.create(nombre="Venta de repuestos")
        Etapa.objects.create(pipeline=pipeline, nombre="Nueva oportunidad", orden=1, tipo=Etapa.Tipo.EN_PROGRESO)

    def test_rutas_de_cotizaciones_requieren_inicio_de_sesion(self):
        response = self.client.get(reverse("cotizaciones:list"), secure=True)
        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('cotizaciones:list')}",
            fetch_redirect_response=False,
        )

    def test_creacion_guarda_al_vendedor_responsable(self):
        self.client.force_login(self.vendedora1)
        response = self.client.post(
            reverse("cotizaciones:create"),
            {
                "cliente": self.cliente.pk,
                "descripcion_repuesto": "Kit de embrague",
                "codigo_producto": "",
                "descuento_pct": "0",
            },
            secure=True,
        )
        self.assertRedirects(response, reverse("cotizaciones:list"), fetch_redirect_response=False)
        cotizacion = Cotizacion.objects.get()
        self.assertEqual(cotizacion.usuario, self.vendedora1)
        self.assertEqual(cotizacion.estado, Cotizacion.Estado.ENVIADA)

    def test_filtro_por_estado(self):
        Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1,
            descripcion_repuesto="Frenos", estado=Cotizacion.Estado.CONFIRMADA,
        )
        Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1,
            descripcion_repuesto="Filtro de aceite", estado=Cotizacion.Estado.PERDIDA,
        )
        self.client.force_login(self.vendedora1)
        response = self.client.get(reverse("cotizaciones:list"), {"estado": "CONFIRMADA"}, secure=True)
        self.assertContains(response, "Frenos")
        self.assertNotContains(response, "Filtro de aceite")

    def test_filtro_por_vendedor(self):
        Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Frenos",
        )
        Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora2, descripcion_repuesto="Bujías",
        )
        self.client.force_login(self.vendedora1)
        response = self.client.get(
            reverse("cotizaciones:list"), {"vendedor": self.vendedora2.pk}, secure=True
        )
        self.assertContains(response, "Bujías")
        self.assertNotContains(response, "Frenos")

    def test_transicion_valida_cambia_estado(self):
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
        )
        self.client.force_login(self.vendedora1)
        self.client.post(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]),
            {"estado": Cotizacion.Estado.CONFIRMADA},
            secure=True,
        )
        cotizacion.refresh_from_db()
        self.assertEqual(cotizacion.estado, Cotizacion.Estado.CONFIRMADA)

    def test_transicion_directa_de_enviada_a_perdida_es_valida(self):
        """El 91% de perdida ocurre antes de confirmar -- ver DAS."""
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
        )
        self.client.force_login(self.vendedora1)
        self.client.post(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]),
            {"estado": Cotizacion.Estado.PERDIDA},
            secure=True,
        )
        cotizacion.refresh_from_db()
        self.assertEqual(cotizacion.estado, Cotizacion.Estado.PERDIDA)

    def test_transicion_invalida_no_cambia_estado(self):
        """No se puede saltar de Enviada directo a Convertida."""
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
        )
        self.client.force_login(self.vendedora1)
        self.client.post(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]),
            {"estado": Cotizacion.Estado.CONVERTIDA},
            secure=True,
        )
        cotizacion.refresh_from_db()
        self.assertEqual(cotizacion.estado, Cotizacion.Estado.ENVIADA)

    def test_estado_terminal_no_admite_mas_transiciones(self):
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
            estado=Cotizacion.Estado.CONVERTIDA,
        )
        self.client.force_login(self.vendedora1)
        self.client.post(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]),
            {"estado": Cotizacion.Estado.ENVIADA},
            secure=True,
        )
        cotizacion.refresh_from_db()
        self.assertEqual(cotizacion.estado, Cotizacion.Estado.CONVERTIDA)

    def test_transicion_invalida_responde_400(self):
        """
        El tablero Kanban distingue exito de rechazo por el status code de
        la respuesta (fetch + res.ok) -- no basta con que el estado no
        cambie, la vista tiene que devolver un error real.
        """
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
        )
        self.client.force_login(self.vendedora1)
        response = self.client.post(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]),
            {"estado": Cotizacion.Estado.CONVERTIDA},
            secure=True,
        )
        self.assertEqual(response.status_code, 400)

    def test_transicion_valida_no_responde_error(self):
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
        )
        self.client.force_login(self.vendedora1)
        response = self.client.post(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]),
            {"estado": Cotizacion.Estado.CONFIRMADA},
            secure=True,
        )
        self.assertEqual(response.status_code, 302)

    def test_update_estado_solo_acepta_post(self):
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
        )
        self.client.force_login(self.vendedora1)
        response = self.client.get(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]), secure=True
        )
        self.assertEqual(response.status_code, 405)

    def test_transicion_actualiza_el_campo_actualizado(self):
        """`dias_desde_actualizacion` del tablero depende de este campo, no de `fecha`."""
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.vendedora1, descripcion_repuesto="Kit de embrague",
        )
        actualizado_antes = cotizacion.actualizado
        self.client.force_login(self.vendedora1)
        self.client.post(
            reverse("cotizaciones:update_estado", args=[cotizacion.pk]),
            {"estado": Cotizacion.Estado.CONFIRMADA},
            secure=True,
        )
        cotizacion.refresh_from_db()
        self.assertGreater(cotizacion.actualizado, actualizado_antes)

    def test_creacion_con_next_tablero_redirige_a_negocios(self):
        """El mini-formulario con next=tablero ahora redirige al pipeline de negocios."""
        self.client.force_login(self.vendedora1)
        response = self.client.post(
            reverse("cotizaciones:create"),
            {
                "cliente": self.cliente.pk,
                "descripcion_repuesto": "Kit de embrague",
                "codigo_producto": "",
                "descuento_pct": "0",
                "next": "tablero",
            },
            secure=True,
        )
        self.assertRedirects(response, reverse("oportunidades:negocios"), fetch_redirect_response=False)

    def test_creacion_con_next_invalido_redirige_a_list(self):
        """Whitelist cerrada: cualquier valor no reconocido cae al destino por defecto."""
        self.client.force_login(self.vendedora1)
        response = self.client.post(
            reverse("cotizaciones:create"),
            {
                "cliente": self.cliente.pk,
                "descripcion_repuesto": "Kit de embrague",
                "codigo_producto": "",
                "descuento_pct": "0",
                "next": "https://evil.example.com/",
            },
            secure=True,
        )
        self.assertRedirects(response, reverse("cotizaciones:list"), fetch_redirect_response=False)


class NegociosPipelineTests(TestCase):
    """Tests del pipeline de negocios (antes TableroVendedorTests, ahora en /negocios/)."""

    def setUp(self):
        from oportunidades.models import Etapa, Pipeline
        User = get_user_model()
        self.vendedora1 = User.objects.create_user(username="vendedora1", password="clave123")
        self.vendedora2 = User.objects.create_user(username="vendedora2", password="clave123")
        self.cliente = Cliente.objects.create(nombre="Taller Norte", telefono="999111222")
        pipeline = Pipeline.objects.create(nombre="Venta de repuestos")
        Etapa.objects.create(pipeline=pipeline, nombre="Nueva oportunidad", orden=1, tipo=Etapa.Tipo.EN_PROGRESO)

    def test_cotizaciones_raiz_redirige_a_negocios(self):
        """/cotizaciones/ ya no es el tablero; redirige a /negocios/."""
        self.client.force_login(self.vendedora1)
        response = self.client.get(reverse("cotizaciones:tablero"), secure=True)
        self.assertRedirects(
            response,
            reverse("oportunidades:negocios"),
            fetch_redirect_response=False,
        )

    def test_cotizaciones_raiz_requiere_inicio_de_sesion(self):
        response = self.client.get(reverse("cotizaciones:tablero"), secure=True)
        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('cotizaciones:tablero')}",
            fetch_redirect_response=False,
        )

    def test_mis_negocios_solo_muestra_oportunidades_del_vendedor_logueado(self):
        """?vista=mis filtra por creado_por — el equipo ve sus propios negocios."""
        crear_oportunidad(cliente=self.cliente, usuario=self.vendedora1, titulo="Kit de embrague propio")
        crear_oportunidad(cliente=self.cliente, usuario=self.vendedora2, titulo="Cotizacion de otra vendedora")
        self.client.force_login(self.vendedora1)
        response = self.client.get(reverse("oportunidades:negocios") + "?vista=mis", secure=True)
        self.assertContains(response, "Kit de embrague propio")
        self.assertNotContains(response, "Cotizacion de otra vendedora")

    def test_negocios_incluye_datos_del_pipeline(self):
        """El template embebe los JSON que monta TableroOportunidades.svelte."""
        self.client.force_login(self.vendedora1)
        response = self.client.get(reverse("oportunidades:negocios"), secure=True)
        self.assertContains(response, 'id="oportunidades-data"')
        self.assertContains(response, 'id="etapas-data"')
        self.assertContains(response, "Nueva oportunidad")

    def test_ninguna_pagina_del_crm_enlaza_a_whatsapp_por_separado(self):
        self.client.force_login(self.vendedora1)
        response = self.client.get(reverse("oportunidades:negocios"), secure=True)
        self.assertNotContains(response, 'href="/whatsapp/"')

    def test_no_existe_ruta_de_whatsapp(self):
        self.client.force_login(self.vendedora1)
        response = self.client.get("/whatsapp/", secure=True)
        self.assertEqual(response.status_code, 404)
