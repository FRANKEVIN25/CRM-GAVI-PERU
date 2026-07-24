from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from clientes.models import Cliente
from oportunidades.models import Actividad, Etapa, Lead, Oportunidad, Pipeline

from .models import Tarea
from .services import completar_tarea


class TareaModelTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username="vendedora", password="clave-segura")
        self.lead = Lead.objects.create(nombre_contacto="Taller Norte", telefono="999111222")
        self.ct_lead = ContentType.objects.get_for_model(Lead)

    def _tarea(self, **kwargs):
        defaults = dict(
            content_type=self.ct_lead,
            object_id=self.lead.pk,
            titulo="Llamar para confirmar pedido",
            tipo=Tarea.Tipo.LLAMADA,
            fecha_vencimiento=timezone.now() + timedelta(days=1),
        )
        defaults.update(kwargs)
        return Tarea.objects.create(**defaults)

    def test_estado_inicial_es_pendiente(self):
        tarea = self._tarea()
        self.assertEqual(tarea.estado, Tarea.Estado.PENDIENTE)

    def test_marcar_vencidas_actualiza_tareas_atrasadas(self):
        tarea = self._tarea(fecha_vencimiento=timezone.now() - timedelta(hours=1))
        Tarea.objects.marcar_vencidas()
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, Tarea.Estado.VENCIDA)

    def test_marcar_vencidas_no_toca_completadas(self):
        tarea = self._tarea(
            fecha_vencimiento=timezone.now() - timedelta(hours=1),
            estado=Tarea.Estado.COMPLETADA,
        )
        Tarea.objects.marcar_vencidas()
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, Tarea.Estado.COMPLETADA)


class CompletarTareaServiceTests(TestCase):
    def setUp(self):
        self.lead = Lead.objects.create(nombre_contacto="Taller Norte", telefono="999111222")
        self.ct_lead = ContentType.objects.get_for_model(Lead)

    def _tarea(self, tipo=Tarea.Tipo.LLAMADA):
        return Tarea.objects.create(
            content_type=self.ct_lead,
            object_id=self.lead.pk,
            titulo="Confirmar pedido",
            tipo=tipo,
            fecha_vencimiento=timezone.now() + timedelta(days=1),
        )

    def test_completar_cambia_estado(self):
        tarea = self._tarea()
        completar_tarea(tarea)
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, Tarea.Estado.COMPLETADA)

    def test_completar_llamada_genera_actividad_llamada(self):
        tarea = self._tarea(tipo=Tarea.Tipo.LLAMADA)
        completar_tarea(tarea)
        actividad = Actividad.objects.get(content_type=self.ct_lead, object_id=self.lead.pk)
        self.assertEqual(actividad.tipo, Actividad.Tipo.LLAMADA)

    def test_completar_correo_genera_actividad_nota(self):
        tarea = self._tarea(tipo=Tarea.Tipo.CORREO)
        completar_tarea(tarea)
        actividad = Actividad.objects.get(content_type=self.ct_lead, object_id=self.lead.pk)
        self.assertEqual(actividad.tipo, Actividad.Tipo.NOTA)

    def test_completar_otro_no_genera_actividad(self):
        tarea = self._tarea(tipo=Tarea.Tipo.OTRO)
        completar_tarea(tarea)
        self.assertEqual(Actividad.objects.count(), 0)

    def test_completar_tarea_ya_completada_lanza_error(self):
        tarea = self._tarea()
        completar_tarea(tarea)
        with self.assertRaises(ValidationError):
            completar_tarea(tarea)
