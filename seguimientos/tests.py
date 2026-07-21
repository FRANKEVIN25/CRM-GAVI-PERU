from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente

from .models import Seguimiento

@override_settings(SECURE_SSL_REDIRECT=False)
class SeguimientosViewsTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(username="vendedora", password="clave-segura")
        self.cliente = Cliente.objects.create(
            nombre="Taller Norte", telefono="999111222", creado_por=self.usuario
        )
        self.client.force_login(self.usuario)

    def test_listado_marca_recordatorios_atrasados_como_vencidos(self):
        seguimiento = Seguimiento.objects.create(
            cliente=self.cliente,
            usuario=self.usuario,
            fecha_recordatorio=timezone.now() - timedelta(hours=1),
        )

        response = self.client.get(reverse("seguimientos:listado"))

        self.assertEqual(response.status_code, 200)
        seguimiento.refresh_from_db()
        self.assertEqual(seguimiento.estado, Seguimiento.Estado.VENCIDO)

    def test_crear_y_marcar_cumplido(self):
        fecha = timezone.localtime(timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(reverse("seguimientos:crear"), {
            "cliente": self.cliente.pk,
            "fecha_recordatorio": fecha,
        })

        self.assertRedirects(response, reverse("seguimientos:listado"))
        seguimiento = Seguimiento.objects.get(cliente=self.cliente)
        response = self.client.post(reverse("seguimientos:marcar_cumplido", args=[seguimiento.pk]))

        self.assertRedirects(response, reverse("seguimientos:listado"))
        seguimiento.refresh_from_db()
        self.assertEqual(seguimiento.estado, Seguimiento.Estado.CUMPLIDO)
