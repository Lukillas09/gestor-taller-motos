import json
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import resolve, reverse
from django.utils import timezone
from django.views.defaults import (
    bad_request,
    page_not_found,
    permission_denied,
    server_error,
)

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

    def test_busqueda_global_requiere_login(self):
        response = self.client.get(reverse("core:search"), {"q": "Honda"})

        self.assertEqual(response.status_code, 302)
        destino = urlparse(response.url)
        self.assertEqual(destino.path, reverse("login"))
        self.assertEqual(parse_qs(destino.query)["next"], ["/buscar/?q=Honda"])

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

    def test_login_rechaza_redireccion_externa(self):
        response = self.client.post(
            f'{reverse("login")}?next=https://example.com/salida',
            {"username": "mecanico", "password": "clave-segura"},
        )

        self.assertRedirects(response, reverse("core:dashboard"))


class ProductionReadinessTests(TestCase):
    def test_urls_compartidas_de_mantenimientos_resuelven_sin_colisiones(self):
        casos = {
            "/mantenimientos/": "notificaciones:alertas",
            "/mantenimientos/1/2/contactar/": "notificaciones:contactar",
            "/mantenimientos/configuracion/": "mantenimientos:configuracion",
            "/mantenimientos/configuracion/nuevo/": "mantenimientos:tipo_create",
        }

        for ruta, vista_esperada in casos.items():
            with self.subTest(ruta=ruta):
                self.assertEqual(resolve(ruta).view_name, vista_esperada)

    def test_configuracion_de_tests_no_usa_database_url(self):
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )
        self.assertIn("memory", str(settings.DATABASES["default"]["NAME"]))

    def test_staticfiles_de_tests_no_requiere_manifiesto_de_produccion(self):
        self.assertEqual(
            settings.STORAGES["staticfiles"]["BACKEND"],
            "django.contrib.staticfiles.storage.StaticFilesStorage",
        )
        self.assertFalse(hasattr(settings, "STATICFILES_STORAGE"))

    def test_manifest_pwa_es_valido_y_sus_iconos_existen(self):
        manifest_path = settings.BASE_DIR / "static" / "manifest.webmanifest"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(manifest["start_url"], "/")
        self.assertEqual(manifest["scope"], "/")
        self.assertEqual(manifest["display"], "standalone")
        self.assertTrue(manifest["icons"])
        for icono in manifest["icons"]:
            ruta_relativa = icono["src"].removeprefix("/static/")
            self.assertTrue((settings.BASE_DIR / "static" / ruta_relativa).is_file())

    def test_service_worker_se_sirve_desde_raiz_y_solo_cachea_estaticos(self):
        response = self.client.get(reverse("service-worker"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response.headers["Content-Type"])
        contenido = b"".join(response.streaming_content).decode("utf-8")
        self.assertIn('url.pathname.startsWith("/static/")', contenido)
        self.assertIn('event.request.method !== "GET"', contenido)
        self.assertIn("url.origin !== self.location.origin", contenido)
        self.assertNotIn("/exportaciones/", contenido)

    def test_paginas_de_error_no_exponen_detalles_tecnicos(self):
        request = RequestFactory().get("/ruta-inexistente/")
        detalle_sensible = "detalle-interno-no-visible"
        respuestas = [
            bad_request(request, Exception(detalle_sensible)),
            permission_denied(request, Exception(detalle_sensible)),
            page_not_found(request, Exception(detalle_sensible)),
            server_error(request),
        ]

        for respuesta, codigo in zip(respuestas, (400, 403, 404, 500), strict=True):
            with self.subTest(codigo=codigo):
                contenido = respuesta.content.decode("utf-8")
                self.assertEqual(respuesta.status_code, codigo)
                self.assertIn(f"ERROR {codigo}", contenido)
                self.assertNotIn(detalle_sensible, contenido)
