from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Cliente, Interaccion, Vehiculo


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


class InteraccionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.vendedora1 = User.objects.create_user(username="vendedora1", password="clave123")
        self.vendedora2 = User.objects.create_user(username="vendedora2", password="clave123")
        self.cliente = Cliente.objects.create(
            nombre="Taller Sur", telefono="999222333", creado_por=self.vendedora1
        )

    def test_cualquier_usuario_puede_registrar_interaccion(self):
        """Vendedora2 puede registrar una interacción en un cliente creado por vendedora1."""
        self.client.force_login(self.vendedora2)
        response = self.client.post(
            reverse("clientes:add_interaccion", args=[self.cliente.pk]),
            {"canal": "LLAMADA", "nota": "Confirmó pedido de frenos"},
            secure=True,
        )
        self.assertRedirects(
            response,
            reverse("clientes:detail", args=[self.cliente.pk]),
            fetch_redirect_response=False,
        )
        interaccion = self.cliente.interacciones.get()
        self.assertEqual(interaccion.usuario, self.vendedora2)
        self.assertEqual(interaccion.nota, "Confirmó pedido de frenos")

    def test_historial_visible_en_ficha(self):
        """La ficha muestra las notas de todas las interacciones del cliente."""
        Interaccion.objects.create(
            cliente=self.cliente,
            usuario=self.vendedora1,
            canal="WHATSAPP",
            nota="Preguntó por aceite de motor",
        )
        self.client.force_login(self.vendedora1)
        response = self.client.get(
            reverse("clientes:detail", args=[self.cliente.pk]), secure=True
        )
        self.assertContains(response, "Preguntó por aceite de motor")
        self.assertContains(response, "WhatsApp")

    def test_registrar_interaccion_requiere_autenticacion(self):
        """Un usuario no autenticado es redirigido al login y no se crea nada."""
        response = self.client.post(
            reverse("clientes:add_interaccion", args=[self.cliente.pk]),
            {"canal": "LLAMADA", "nota": "Test sin login"},
            secure=True,
        )
        self.assertRedirects(
            response,
            f"/accounts/login/?next={reverse('clientes:add_interaccion', args=[self.cliente.pk])}",
            fetch_redirect_response=False,
        )
        self.assertEqual(self.cliente.interacciones.count(), 0)
