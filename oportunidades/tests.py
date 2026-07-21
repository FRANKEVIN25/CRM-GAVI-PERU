from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from clientes.models import Cliente
from cotizaciones.models import Cotizacion

from .models import CambioEtapa, Etapa, Pipeline
from .services import cerrar_oportunidad_ganada, crear_oportunidad, mover_oportunidad_de_etapa


class OportunidadesServicesTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username="ventas", password="clave-segura")
        self.cliente = Cliente.objects.create(nombre="Taller Norte", telefono="999111222", creado_por=self.usuario)
        self.pipeline = Pipeline.objects.get(nombre="Venta de repuestos")
        self.inicial = self.pipeline.etapas.get(nombre="Nueva oportunidad")
        self.cotizada = self.pipeline.etapas.get(nombre="Cotización enviada")
        self.ganada = self.pipeline.etapas.get(tipo=Etapa.Tipo.GANADA)

    def test_crea_y_registra_historial_inicial(self):
        oportunidad = crear_oportunidad(cliente=self.cliente, usuario=self.usuario)

        self.assertEqual(oportunidad.etapa, self.inicial)
        self.assertEqual(oportunidad.estado, Etapa.Tipo.EN_PROGRESO)
        self.assertEqual(CambioEtapa.objects.filter(oportunidad=oportunidad).count(), 1)

    def test_no_permite_mover_a_etapa_de_cierre_sin_servicio_de_cierre(self):
        oportunidad = crear_oportunidad(cliente=self.cliente, usuario=self.usuario)

        with self.assertRaises(ValidationError):
            mover_oportunidad_de_etapa(
                oportunidad_id=oportunidad.pk, etapa_nueva=self.ganada, usuario=self.usuario,
            )

    def test_ganar_exige_cotizacion_confirmada_y_convierte_solo_la_vigente(self):
        oportunidad = crear_oportunidad(cliente=self.cliente, usuario=self.usuario)
        mover_oportunidad_de_etapa(oportunidad_id=oportunidad.pk, etapa_nueva=self.cotizada, usuario=self.usuario)
        cotizacion = Cotizacion.objects.create(
            cliente=self.cliente, usuario=self.usuario, oportunidad=oportunidad,
            descripcion_repuesto="Kit de embrague", estado=Cotizacion.Estado.CONFIRMADA,
        )

        cerrar_oportunidad_ganada(oportunidad_id=oportunidad.pk, etapa_ganada=self.ganada, usuario=self.usuario)

        oportunidad.refresh_from_db()
        cotizacion.refresh_from_db()
        self.assertEqual(oportunidad.etapa, self.ganada)
        self.assertEqual(cotizacion.estado, Cotizacion.Estado.CONVERTIDA)
