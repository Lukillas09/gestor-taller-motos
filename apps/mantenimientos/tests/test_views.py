from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.mantenimientos.models import MantenimientoRealizado, TipoMantenimiento
from apps.motos.models import Moto
from apps.servicios.models import Servicio


class MantenimientoViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username="mecanico",
            password="clave-segura",
        )
        cls.tipo_vencido = TipoMantenimiento.objects.get(
            nombre="Cambio de aceite"
        )
        cls.tipo_vencido.genera_recordatorio = True
        cls.tipo_vencido.intervalo_km = 5000
        cls.tipo_vencido.aviso_km = 500
        cls.tipo_vencido.save()
        cls.tipo_proximo = TipoMantenimiento.objects.get(
            nombre="Cadena / transmisión"
        )
        cls.tipo_proximo.genera_recordatorio = True
        cls.tipo_proximo.intervalo_km = 5000
        cls.tipo_proximo.aviso_km = 500
        cls.tipo_proximo.save()

        cls.cliente_vencido = Cliente.objects.create(
            nombre="Carlos",
            apellido="González",
            telefono="261 555-1000",
        )
        cls.moto_vencida = Moto.objects.create(
            cliente=cls.cliente_vencido,
            patente="AF123XY",
            marca="Honda",
            modelo="Tornado",
            kilometraje_actual=20000,
        )
        cls.cliente_proximo = Cliente.objects.create(
            nombre="Martina",
            apellido="Pérez",
            telefono="260 412-3456",
        )
        cls.moto_proxima = Moto.objects.create(
            cliente=cls.cliente_proximo,
            patente="AG456TR",
            marca="Yamaha",
            modelo="FZ",
            kilometraje_actual=14600,
        )
        fecha = timezone.localdate() - timedelta(days=90)
        servicio_vencido = Servicio.objects.create(
            moto=cls.moto_vencida,
            fecha=fecha,
            kilometraje=10000,
        )
        servicio_proximo = Servicio.objects.create(
            moto=cls.moto_proxima,
            fecha=fecha,
            kilometraje=10000,
        )
        MantenimientoRealizado.objects.create(
            servicio=servicio_vencido,
            tipo_mantenimiento=cls.tipo_vencido,
        )
        MantenimientoRealizado.objects.create(
            servicio=servicio_proximo,
            tipo_mantenimiento=cls.tipo_proximo,
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def datos_tipo(self, **cambios):
        datos = {
            "nombre": "Regulación de válvulas",
            "descripcion": "Control programado",
            "activo": "on",
            "genera_recordatorio": "on",
            "intervalo_meses": "12",
            "intervalo_km": "6000",
            "aviso_dias": "30",
            "aviso_km": "500",
        }
        datos.update(cambios)
        return datos

    def test_todas_las_vistas_requieren_login(self):
        anonimo = TestClient()
        solicitudes = (
            ("get", reverse("notificaciones:alertas")),
            ("get", reverse("mantenimientos:configuracion")),
            ("get", reverse("mantenimientos:tipo_create")),
            (
                "get",
                reverse(
                    "mantenimientos:tipo_update",
                    args=(self.tipo_vencido.pk,),
                ),
            ),
            (
                "post",
                reverse(
                    "mantenimientos:tipo_archive",
                    args=(self.tipo_vencido.pk,),
                ),
            ),
            (
                "post",
                reverse(
                    "mantenimientos:tipo_restore",
                    args=(self.tipo_vencido.pk,),
                ),
            ),
        )

        for metodo, url in solicitudes:
            with self.subTest(url=url):
                response = getattr(anonimo, metodo)(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(reverse("login")))

    def test_listado_muestra_alertas_ordenadas_por_prioridad(self):
        response = self.client.get(reverse("notificaciones:alertas"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["alertas"]), 2)
        self.assertEqual(response.context["alertas"][0].moto, self.moto_vencida)
        self.assertContains(response, "Vencido")
        self.assertContains(response, "Próximo")
        self.assertContains(response, "AF123XY")
        self.assertContains(response, "AG456TR")

    def test_filtros_por_estado_y_tipo(self):
        vencidos = self.client.get(
            reverse("notificaciones:alertas"),
            {"estado": "VENCIDO"},
        )
        proximos = self.client.get(
            reverse("notificaciones:alertas"),
            {"estado": "PROXIMO"},
        )
        por_tipo = self.client.get(
            reverse("notificaciones:alertas"),
            {"tipo": str(self.tipo_proximo.pk)},
        )

        self.assertEqual([a.moto for a in vencidos.context["alertas"]], [self.moto_vencida])
        self.assertEqual([a.moto for a in proximos.context["alertas"]], [self.moto_proxima])
        self.assertEqual([a.moto for a in por_tipo.context["alertas"]], [self.moto_proxima])

    def test_busqueda_por_patente_moto_cliente_y_telefono(self):
        consultas = ("ag-456-tr", "Yamaha", "Martina Perez", "2604")

        for termino in consultas:
            with self.subTest(termino=termino):
                response = self.client.get(
                    reverse("notificaciones:alertas"),
                    {"q": termino},
                )
                self.assertEqual(
                    [alerta.moto for alerta in response.context["alertas"]],
                    [self.moto_proxima],
                )

    def test_htmx_devuelve_solo_lista_y_fallback_devuelve_pagina(self):
        htmx = self.client.get(
            reverse("notificaciones:alertas"),
            {"estado": "VENCIDO"},
            HTTP_HX_REQUEST="true",
        )
        normal = self.client.get(
            reverse("notificaciones:alertas"),
            {"estado": "VENCIDO"},
        )

        self.assertTemplateUsed(
            htmx,
            "mantenimientos/partials/lista_alertas.html",
        )
        self.assertNotContains(htmx, "<!doctype html>")
        self.assertTemplateUsed(normal, "mantenimientos/alertas.html")
        self.assertContains(normal, "<!doctype html>")

    def test_configuracion_muestra_reglas_y_estado(self):
        response = self.client.get(reverse("mantenimientos:configuracion"))

        self.assertContains(response, "Cambio de aceite")
        self.assertContains(response, "Cadena / transmisión")
        self.assertContains(response, "Con alertas", count=2)

    def test_crea_tipo_desde_la_aplicacion(self):
        response = self.client.post(
            reverse("mantenimientos:tipo_create"),
            self.datos_tipo(),
        )

        tipo = TipoMantenimiento.objects.get(nombre="Regulación de válvulas")
        self.assertRedirects(
            response,
            reverse("mantenimientos:tipo_update", args=(tipo.pk,)),
        )
        self.assertEqual(tipo.intervalo_meses, 12)
        self.assertEqual(tipo.intervalo_km, 6000)

    def test_creacion_invalida_muestra_errores(self):
        response = self.client.post(
            reverse("mantenimientos:tipo_create"),
            self.datos_tipo(intervalo_meses="", intervalo_km=""),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("genera_recordatorio", response.context["form"].errors)

    def test_edita_tipo_y_recalcula_configuracion(self):
        response = self.client.post(
            reverse(
                "mantenimientos:tipo_update",
                args=(self.tipo_proximo.pk,),
            ),
            self.datos_tipo(
                nombre="Cadena reforzada",
                intervalo_meses="",
                intervalo_km="7000",
                aviso_km="700",
            ),
        )

        self.tipo_proximo.refresh_from_db()
        self.assertRedirects(response, reverse("mantenimientos:configuracion"))
        self.assertEqual(self.tipo_proximo.nombre, "Cadena reforzada")
        self.assertEqual(self.tipo_proximo.intervalo_km, 7000)

    def test_desactivar_y_restaurar_solo_admiten_post(self):
        archive_url = reverse(
            "mantenimientos:tipo_archive",
            args=(self.tipo_vencido.pk,),
        )
        restore_url = reverse(
            "mantenimientos:tipo_restore",
            args=(self.tipo_vencido.pk,),
        )

        self.assertEqual(self.client.get(archive_url).status_code, 405)
        self.client.post(archive_url)
        self.tipo_vencido.refresh_from_db()
        self.assertFalse(self.tipo_vencido.activo)

        self.assertEqual(self.client.get(restore_url).status_code, 405)
        self.client.post(restore_url)
        self.tipo_vencido.refresh_from_db()
        self.assertTrue(self.tipo_vencido.activo)

    def test_estado_vacio_distingue_falta_de_reglas(self):
        TipoMantenimiento.objects.update(genera_recordatorio=False)

        response = self.client.get(reverse("notificaciones:alertas"))

        self.assertContains(response, "Configurá la primera regla")
        self.assertEqual(response.context["resumen"].alertas, ())

    def test_estado_vacio_informa_cuando_no_hay_alertas(self):
        Moto.objects.filter(pk=self.moto_vencida.pk).update(
            kilometraje_actual=10000
        )
        Moto.objects.filter(pk=self.moto_proxima.pk).update(
            kilometraje_actual=10000
        )

        response = self.client.get(reverse("notificaciones:alertas"))

        self.assertContains(response, "Todo al día")
        self.assertEqual(response.context["resumen"].alertas, ())
