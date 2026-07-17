from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Cliente, Vehiculo


class ClienteViewsTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="vendedora", password="clave-segura-123"
        )
        self.cliente = Cliente.objects.create(
            nombre="Taller Norte", telefono="999111222", creado_por=self.usuario
        )
        Vehiculo.objects.create(cliente=self.cliente, placa="ABC123", modelo="Hilux")

    def test_rutas_de_clientes_requieren_inicio_de_sesion(self):
        response = self.client.get(reverse("clientes:search"), secure=True)
        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('clientes:search')}",
            fetch_redirect_response=False,
        )

    def test_busca_por_nombre_telefono_o_placa(self):
        self.client.force_login(self.usuario)
        for termino in ("Norte", "999111222", "abc123"):
            response = self.client.get(reverse("clientes:search"), {"q": termino}, secure=True)
            self.assertContains(response, "Taller Norte")

    def test_advierte_y_no_crea_duplicado_por_placa(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse("clientes:create"),
            {
                "nombre": "Otro nombre",
                "telefono": "988777666",
                "segmento": Cliente.Segmento.CONSUMO,
                "placa": "abc123",
                "modelo": "Otro",
            },
            secure=True,
        )
        self.assertContains(response, "Ya existe al menos un cliente")
        self.assertEqual(Cliente.objects.count(), 1)

    def test_creacion_guarda_usuario_responsable(self):
        self.client.force_login(self.usuario)
        response = self.client.post(
            reverse("clientes:create"),
            {
                "nombre": "Cliente Nuevo",
                "telefono": "988777666",
                "segmento": Cliente.Segmento.CONSUMO,
                "placa": "XYZ456",
                "modelo": "Yaris",
            },
            secure=True,
        )
        cliente = Cliente.objects.get(nombre="Cliente Nuevo")
        self.assertRedirects(
            response,
            reverse("clientes:detail", args=[cliente.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(cliente.creado_por, self.usuario)
        self.assertEqual(cliente.vehiculos.get().creado_por, self.usuario)
