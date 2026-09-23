from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.motos.models import Moto


class ClienteViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="mecanico", password="clave-segura"
        )
        cls.cliente = Cliente.objects.create(
            nombre="Carlos",
            apellido="González",
            telefono="260 4123456",
        )
        cls.archivado = Cliente.objects.create(nombre="Martín", activo=False)
        cls.moto_activa = Moto.objects.create(
            cliente=cls.cliente,
            patente="AF123XY",
            marca="Honda",
            modelo="Tornado XR250",
        )
        cls.moto_archivada = Moto.objects.create(
            cliente=cls.cliente,
            patente="AG456TR",
            marca="Yamaha",
            modelo="FZ",
            activo=False,
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_todas_las_vistas_requieren_login(self):
        cliente_anonimo = TestClient()
        solicitudes = (
            ("get", reverse("clientes:list")),
            ("get", reverse("clientes:create")),
            ("get", reverse("clientes:detail", args=(self.cliente.pk,))),
            ("get", reverse("clientes:update", args=(self.cliente.pk,))),
            ("post", reverse("clientes:archive", args=(self.cliente.pk,))),
            ("post", reverse("clientes:restore", args=(self.archivado.pk,))),
        )

        for metodo, url in solicitudes:
            with self.subTest(url=url):
                response = getattr(cliente_anonimo, metodo)(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("login")))

    def test_listado_muestra_activos_con_cantidad_de_motos(self):
        response = self.client.get(reverse("clientes:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carlos González")
        self.assertContains(response, "1 moto activa")
        self.assertNotContains(response, "Martín")

    def test_listado_de_archivados_y_restauracion_disponible(self):
        response = self.client.get(
            reverse("clientes:list"), {"estado": "archivados"}
        )

        self.assertContains(response, "Martín")
        self.assertNotContains(response, "Carlos González")
        self.assertContains(response, "Restaurar")

    def test_busqueda_por_nombre_y_telefono_sin_formato(self):
        por_nombre = self.client.get(reverse("clientes:list"), {"q": "González"})
        por_telefono = self.client.get(reverse("clientes:list"), {"q": "2604"})

        self.assertContains(por_nombre, "Carlos González")
        self.assertContains(por_telefono, "Carlos González")

    def test_busqueda_htmx_devuelve_solo_el_parcial(self):
        response = self.client.get(
            reverse("clientes:list"),
            {"q": "Carlos"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "clientes/partials/lista.html")
        self.assertNotContains(response, "<!doctype html>")

    def test_crear_cliente_redirige_al_detalle_y_muestra_mensaje(self):
        response = self.client.post(
            reverse("clientes:create"),
            {
                "nombre": "  Ana  María ",
                "apellido": "López",
                "telefono": "260 4999999",
                "email": "ana@example.com",
                "direccion": "Calle 1",
                "observaciones": "Prefiere llamadas por la tarde.",
            },
            follow=True,
        )

        cliente = Cliente.objects.get(email="ana@example.com")
        self.assertRedirects(response, reverse("clientes:detail", args=(cliente.pk,)))
        self.assertContains(response, "Cliente creado correctamente.")
        self.assertEqual(cliente.nombre, "Ana María")

    def test_crear_cliente_rechaza_nombre_en_blanco(self):
        response = self.client.post(reverse("clientes:create"), {"nombre": "   "})

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "nombre", "Ingresá el nombre del cliente.")

    def test_detalle_muestra_solo_motos_activas(self):
        response = self.client.get(
            reverse("clientes:detail", args=(self.cliente.pk,))
        )

        self.assertContains(response, "Honda Tornado XR250")
        self.assertContains(response, "AF123XY")
        self.assertNotContains(response, "AG456TR")
        self.assertContains(
            response,
            f"{reverse('motos:create')}?cliente={self.cliente.pk}",
        )

    def test_editar_cliente(self):
        response = self.client.post(
            reverse("clientes:update", args=(self.cliente.pk,)),
            {
                "nombre": "Carlos",
                "apellido": "González",
                "telefono": "260 4000000",
                "email": "",
                "direccion": "",
                "observaciones": "",
            },
            follow=True,
        )

        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.telefono, "260 4000000")
        self.assertContains(response, "Cliente actualizado correctamente.")

    def test_archivar_es_post_y_no_modifica_motos(self):
        url = reverse("clientes:archive", args=(self.cliente.pk,))

        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, follow=True)

        self.cliente.refresh_from_db()
        self.moto_activa.refresh_from_db()
        self.assertFalse(self.cliente.activo)
        self.assertTrue(self.moto_activa.activo)
        self.assertContains(response, "Sus motos conservaron su estado actual")

    def test_restaurar_es_post(self):
        url = reverse("clientes:restore", args=(self.archivado.pk,))

        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url, follow=True)

        self.archivado.refresh_from_db()
        self.assertTrue(self.archivado.activo)
        self.assertContains(response, "Cliente restaurado.")

    def test_id_inexistente_devuelve_404(self):
        response = self.client.get(reverse("clientes:detail", args=(999999,)))

        self.assertEqual(response.status_code, 404)

    def test_archivado_requiere_csrf(self):
        cliente_csrf = TestClient(enforce_csrf_checks=True)
        cliente_csrf.force_login(self.usuario)

        response = cliente_csrf.post(
            reverse("clientes:archive", args=(self.cliente.pk,))
        )

        self.assertEqual(response.status_code, 403)
