from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.motos.models import Moto


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="mecanico", password="clave-segura"
        )

    def test_dashboard_requiere_login(self):
        response = self.client.get(reverse("core:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('core:dashboard')}",
        )

    def test_dashboard_muestra_conteos_activos(self):
        activo = Cliente.objects.create(nombre="Carlos")
        Cliente.objects.create(nombre="Archivado", activo=False)
        Moto.objects.create(cliente=activo, marca="Honda", modelo="Wave")
        Moto.objects.create(
            cliente=activo, marca="Yamaha", modelo="FZ", activo=False
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MotoService")
        self.assertContains(response, "Clientes")
        self.assertContains(response, "Motos")
        self.assertEqual(response.context["cards"][2]["value"], 1)
        self.assertEqual(response.context["cards"][3]["value"], 1)
        self.assertTemplateUsed(response, "core/dashboard.html")

    def test_busqueda_global_encuentra_clientes_y_motos(self):
        cliente = Cliente.objects.create(
            nombre="Carlos", apellido="González", telefono="260 4123456"
        )
        Moto.objects.create(
            cliente=cliente,
            patente="AF123XY",
            marca="Honda",
            modelo="Tornado",
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:search"), {"q": "Carlos"})

        self.assertContains(response, "Carlos González")
        self.assertContains(response, "Honda Tornado")


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="mecanico", password="clave-segura"
        )

    def test_login_y_logout(self):
        login_response = self.client.post(
            reverse("login"),
            {"username": "mecanico", "password": "clave-segura"},
        )
        self.assertRedirects(login_response, reverse("core:dashboard"))

        logout_response = self.client.post(reverse("logout"))
        self.assertRedirects(logout_response, reverse("login"))

    def test_login_es_publico_y_admin_sigue_disponible(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 302)
