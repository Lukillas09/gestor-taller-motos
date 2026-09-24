from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.mantenimientos.models import MantenimientoRealizado, TipoMantenimiento
from apps.motos.models import Moto
from apps.servicios.models import Servicio


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

    def test_dashboard_muestra_solo_los_ultimos_cinco_servicios(self):
        cliente = Cliente.objects.create(nombre="Carlos")
        moto = Moto.objects.create(cliente=cliente, marca="Honda", modelo="Wave")
        servicios = [Servicio.objects.create(moto=moto) for _ in range(6)]
        MantenimientoRealizado.objects.create(
            servicio=servicios[-1],
            tipo_mantenimiento=TipoMantenimiento.objects.get(
                nombre="Cambio de aceite"
            ),
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(
            list(response.context["ultimos_servicios"]),
            servicios[:0:-1],
        )
        self.assertContains(response, "+ Servicio")
        self.assertContains(response, "Cambio de aceite")

    def test_dashboard_muestra_conteos_reales_y_prioriza_vencidos(self):
        aceite = TipoMantenimiento.objects.get(nombre="Cambio de aceite")
        aceite.genera_recordatorio = True
        aceite.intervalo_km = 5000
        aceite.aviso_km = 500
        aceite.save()
        cadena = TipoMantenimiento.objects.get(nombre="Cadena / transmisión")
        cadena.genera_recordatorio = True
        cadena.intervalo_km = 5000
        cadena.aviso_km = 500
        cadena.save()
        sin_registro = TipoMantenimiento.objects.get(nombre="Batería")
        sin_registro.genera_recordatorio = True
        sin_registro.intervalo_meses = 12
        sin_registro.save()
        cliente = Cliente.objects.create(nombre="Carlos")
        moto_vencida = Moto.objects.create(
            cliente=cliente,
            marca="Honda",
            modelo="Tornado",
            kilometraje_actual=20000,
        )
        moto_proxima = Moto.objects.create(
            cliente=cliente,
            marca="Yamaha",
            modelo="FZ",
            kilometraje_actual=14600,
        )
        servicio_vencido = Servicio.objects.create(
            moto=moto_vencida,
            fecha=timezone.localdate(),
            kilometraje=10000,
        )
        servicio_proximo = Servicio.objects.create(
            moto=moto_proxima,
            fecha=timezone.localdate(),
            kilometraje=10000,
        )
        MantenimientoRealizado.objects.create(
            servicio=servicio_vencido,
            tipo_mantenimiento=aceite,
        )
        MantenimientoRealizado.objects.create(
            servicio=servicio_proximo,
            tipo_mantenimiento=cadena,
        )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.context["cards"][0]["value"], 1)
        self.assertEqual(response.context["cards"][1]["value"], 1)
        self.assertEqual(len(response.context["alertas_prioritarias"]), 2)
        self.assertEqual(
            response.context["alertas_prioritarias"][0].moto,
            moto_vencida,
        )
        self.assertContains(response, "Ver todas las alertas")

    def test_dashboard_limita_alertas_prioritarias_a_cinco(self):
        tipo = TipoMantenimiento.objects.get(nombre="Cambio de aceite")
        tipo.genera_recordatorio = True
        tipo.intervalo_km = 1000
        tipo.save()
        cliente = Cliente.objects.create(nombre="Lucía")
        for indice in range(6):
            moto = Moto.objects.create(
                cliente=cliente,
                marca="Honda",
                modelo=f"Wave {indice}",
                kilometraje_actual=3000,
            )
            servicio = Servicio.objects.create(
                moto=moto,
                fecha=timezone.localdate(),
                kilometraje=1000,
            )
            MantenimientoRealizado.objects.create(
                servicio=servicio,
                tipo_mantenimiento=tipo,
            )
        self.client.force_login(self.usuario)

        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.context["cards"][0]["value"], 6)
        self.assertEqual(len(response.context["alertas_prioritarias"]), 5)


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
