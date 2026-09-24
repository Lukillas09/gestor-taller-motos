from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.mantenimientos.models import MantenimientoRealizado, TipoMantenimiento
from apps.mantenimientos.services import EstadoMantenimiento, construir_estados
from apps.motos.models import Moto
from apps.notificaciones.models import (
    EventoSeguimientoMantenimiento,
    SeguimientoMantenimiento,
)
from apps.notificaciones.services import (
    AccionSeguimientoInvalida,
    AlertaNoOperativa,
    AlertaObsoleta,
    acordar_turno,
    agregar_nota,
    construir_mensaje_whatsapp,
    construir_url_whatsapp,
    marcar_contactado,
    marcar_no_interesado,
    normalizar_numero_whatsapp,
    obtener_resumen_seguimientos,
    posponer_seguimiento,
    reabrir_seguimiento,
    superponer_seguimientos,
)
from apps.servicios.models import Servicio


class SeguimientoServiceTests(TestCase):
    HOY = date(2027, 10, 1)

    @classmethod
    def setUpTestData(cls):
        cls.ahora = timezone.make_aware(datetime(2027, 10, 1, 10, 0))
        cls.usuario = get_user_model().objects.create_user(username="juan")
        cls.carlos = Cliente.objects.create(
            nombre="Carlos",
            apellido="González",
            telefono="+54 9 261 555-1000",
        )
        cls.moto = Moto.objects.create(
            cliente=cls.carlos,
            patente="AF123XY",
            marca="Honda",
            modelo="Tornado XR250",
            kilometraje_actual=20000,
        )
        cls.tipo = TipoMantenimiento.objects.get(nombre="Cambio de aceite")
        cls.tipo.activo = True
        cls.tipo.genera_recordatorio = True
        cls.tipo.intervalo_meses = None
        cls.tipo.intervalo_km = 5000
        cls.tipo.aviso_dias = 0
        cls.tipo.aviso_km = 500
        cls.tipo.save()
        cls.base = cls.registrar_mantenimiento(
            fecha=date(2026, 1, 1),
            kilometraje=10000,
        )

    @classmethod
    def registrar_mantenimiento(
        cls,
        *,
        fecha,
        kilometraje,
        estado=Servicio.Estado.FINALIZADO,
    ):
        servicio = Servicio.objects.create(
            moto=cls.moto,
            fecha=fecha,
            kilometraje=kilometraje,
            estado=estado,
        )
        return MantenimientoRealizado.objects.create(
            servicio=servicio,
            tipo_mantenimiento=cls.tipo,
        )

    def alerta_actual(self):
        self.moto = Moto.objects.select_related("cliente").get(pk=self.moto.pk)
        return construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=self.HOY,
        )[0]

    def kwargs_accion(self, base=None):
        return {
            "moto_id": self.moto.pk,
            "tipo_id": self.tipo.pk,
            "mantenimiento_base_esperado_id": (base or self.base).pk,
            "usuario": self.usuario,
            "hoy": self.HOY,
            "ahora": self.ahora,
        }

    def test_alerta_sin_fila_se_comporta_como_pendiente_sin_escribir(self):
        alerta = self.alerta_actual()

        with self.assertNumQueries(1):
            resultado = superponer_seguimientos(
                (alerta,),
                hoy=self.HOY,
                ahora=self.ahora,
            )[0]

        self.assertEqual(
            resultado.estado_seguimiento,
            SeguimientoMantenimiento.Estado.PENDIENTE,
        )
        self.assertTrue(resultado.es_accionable)
        self.assertEqual(SeguimientoMantenimiento.objects.count(), 0)

    def test_overlay_carga_varios_seguimientos_en_una_consulta(self):
        otra_moto = Moto.objects.create(
            cliente=self.carlos,
            marca="Yamaha",
            modelo="FZ",
            kilometraje_actual=20000,
        )
        servicio = Servicio.objects.create(
            moto=otra_moto,
            fecha=date(2026, 1, 2),
            kilometraje=10000,
        )
        otra_base = MantenimientoRealizado.objects.create(
            servicio=servicio,
            tipo_mantenimiento=self.tipo,
        )
        SeguimientoMantenimiento.objects.create(
            mantenimiento_base=self.base,
            cliente=self.carlos,
            estado=SeguimientoMantenimiento.Estado.CONTACTADO,
        )
        SeguimientoMantenimiento.objects.create(
            mantenimiento_base=otra_base,
            cliente=self.carlos,
            estado=SeguimientoMantenimiento.Estado.NO_INTERESADO,
        )
        alertas = construir_estados(
            (self.moto, otra_moto),
            (self.tipo,),
            hoy=self.HOY,
        )

        with self.assertNumQueries(1):
            resultado = superponer_seguimientos(
                alertas,
                hoy=self.HOY,
                ahora=self.ahora,
            )

        self.assertEqual(len(resultado), 2)

    def test_contactado_crea_seguimiento_evento_y_sigue_accionable(self):
        resultado = marcar_contactado(
            **self.kwargs_accion(),
            nota="Hablé con el cliente.",
        )

        seguimiento = SeguimientoMantenimiento.objects.get()
        evento = EventoSeguimientoMantenimiento.objects.get()
        self.assertEqual(
            seguimiento.estado,
            SeguimientoMantenimiento.Estado.CONTACTADO,
        )
        self.assertEqual(seguimiento.ultimo_contacto_en, self.ahora)
        self.assertEqual(seguimiento.ultimo_contacto_por, self.usuario)
        self.assertEqual(seguimiento.actualizado_por, self.usuario)
        self.assertEqual(seguimiento.observaciones, "Hablé con el cliente.")
        self.assertEqual(
            evento.tipo_evento,
            EventoSeguimientoMantenimiento.Tipo.CONTACTADO,
        )
        self.assertTrue(resultado.es_accionable)
        self.assertEqual(resultado.estado, EstadoMantenimiento.VENCIDO)

    def test_estado_y_evento_se_guardan_atomicamente(self):
        with patch.object(
            EventoSeguimientoMantenimiento.objects,
            "create",
            side_effect=RuntimeError("fallo simulado"),
        ), self.assertRaises(RuntimeError):
            marcar_contactado(**self.kwargs_accion())

        self.assertFalse(SeguimientoMantenimiento.objects.exists())
        self.assertFalse(EventoSeguimientoMantenimiento.objects.exists())

    def test_pospuesto_futuro_se_oculta_y_reaparece_sin_mutar_la_base(self):
        recordar = self.HOY + timedelta(days=9)
        posponer_seguimiento(
            **self.kwargs_accion(),
            pospuesto_hasta=recordar,
        )
        alerta = self.alerta_actual()
        antes = superponer_seguimientos(
            (alerta,),
            hoy=self.HOY,
            ahora=self.ahora,
        )[0]
        al_vencer = superponer_seguimientos(
            (alerta,),
            hoy=recordar,
            ahora=self.ahora + timedelta(days=9),
        )[0]

        self.assertFalse(antes.es_accionable)
        self.assertTrue(al_vencer.es_accionable)
        self.assertTrue(al_vencer.posposicion_vencida)
        seguimiento = SeguimientoMantenimiento.objects.get()
        self.assertEqual(
            seguimiento.estado,
            SeguimientoMantenimiento.Estado.POSPUESTO,
        )
        self.assertEqual(seguimiento.pospuesto_hasta, recordar)

    def test_turno_futuro_se_oculta_y_pasado_reaparece(self):
        turno = self.ahora + timedelta(days=2)
        acordar_turno(**self.kwargs_accion(), turno_para=turno)
        alerta = self.alerta_actual()

        antes = superponer_seguimientos(
            (alerta,), hoy=self.HOY, ahora=self.ahora
        )[0]
        despues = superponer_seguimientos(
            (alerta,), hoy=self.HOY + timedelta(days=2), ahora=turno
        )[0]

        self.assertFalse(antes.es_accionable)
        self.assertTrue(despues.es_accionable)
        self.assertTrue(despues.turno_vencido)

    def test_no_interesado_no_es_accionable_y_reabrir_limpia_fechas(self):
        marcar_no_interesado(**self.kwargs_accion(), nota="No desea hacerlo.")
        no_interesado = obtener_resumen_seguimientos(
            hoy=self.HOY,
            ahora=self.ahora,
        )

        self.assertFalse(no_interesado.alertas[0].es_accionable)
        self.assertEqual(len(no_interesado.no_interesados), 1)

        reabierto = reabrir_seguimiento(
            **self.kwargs_accion(),
            nota="Volvió a consultar.",
        )
        seguimiento = SeguimientoMantenimiento.objects.get()
        self.assertEqual(
            seguimiento.estado,
            SeguimientoMantenimiento.Estado.PENDIENTE,
        )
        self.assertIsNone(seguimiento.pospuesto_hasta)
        self.assertIsNone(seguimiento.turno_para)
        self.assertTrue(reabierto.es_accionable)
        self.assertEqual(
            list(
                seguimiento.eventos.values_list("tipo_evento", flat=True)
            ),
            [
                EventoSeguimientoMantenimiento.Tipo.NO_INTERESADO,
                EventoSeguimientoMantenimiento.Tipo.REABIERTO,
            ],
        )

    def test_no_reabre_un_seguimiento_que_ya_esta_pendiente(self):
        SeguimientoMantenimiento.objects.create(
            mantenimiento_base=self.base,
            cliente=self.carlos,
        )

        with self.assertRaises(AlertaNoOperativa):
            reabrir_seguimiento(**self.kwargs_accion())

        self.assertFalse(EventoSeguimientoMantenimiento.objects.exists())

    def test_acciones_reutilizan_fila_y_preservan_eventos_en_orden(self):
        marcar_contactado(**self.kwargs_accion())
        posponer_seguimiento(
            **self.kwargs_accion(),
            pospuesto_hasta=self.HOY + timedelta(days=7),
        )
        reabrir_seguimiento(**self.kwargs_accion())

        self.assertEqual(SeguimientoMantenimiento.objects.count(), 1)
        eventos = list(
            EventoSeguimientoMantenimiento.objects.values_list(
                "tipo_evento", "usuario_id"
            )
        )
        self.assertEqual(
            eventos,
            [
                (EventoSeguimientoMantenimiento.Tipo.CONTACTADO, self.usuario.pk),
                (EventoSeguimientoMantenimiento.Tipo.POSPUESTO, self.usuario.pk),
                (EventoSeguimientoMantenimiento.Tipo.REABIERTO, self.usuario.pk),
            ],
        )

    def test_nota_conserva_el_estado_y_fecha_operativa(self):
        recordar = self.HOY + timedelta(days=7)
        posponer_seguimiento(
            **self.kwargs_accion(),
            pospuesto_hasta=recordar,
        )

        agregar_nota(**self.kwargs_accion(), nota="Llamar por la tarde.")

        seguimiento = SeguimientoMantenimiento.objects.get()
        self.assertEqual(
            seguimiento.estado,
            SeguimientoMantenimiento.Estado.POSPUESTO,
        )
        self.assertEqual(seguimiento.pospuesto_hasta, recordar)
        self.assertEqual(seguimiento.observaciones, "Llamar por la tarde.")

    def test_fechas_invalidas_se_rechazan_en_el_servicio(self):
        with self.assertRaises(AccionSeguimientoInvalida):
            posponer_seguimiento(
                **self.kwargs_accion(),
                pospuesto_hasta=self.HOY,
            )
        with self.assertRaises(AccionSeguimientoInvalida):
            acordar_turno(
                **self.kwargs_accion(),
                turno_para=self.ahora,
            )
        with self.assertRaises(AccionSeguimientoInvalida):
            acordar_turno(
                **self.kwargs_accion(),
                turno_para=datetime(2027, 10, 2, 10, 0),
            )

    def test_pagina_obsoleta_no_escribe_sobre_un_ciclo_nuevo(self):
        nuevo = self.registrar_mantenimiento(
            fecha=date(2027, 1, 1),
            kilometraje=15000,
        )

        with self.assertRaises(AlertaObsoleta):
            marcar_contactado(**self.kwargs_accion(base=self.base))

        self.assertEqual(nuevo.seguimientos.count(), 0)
        self.assertFalse(SeguimientoMantenimiento.objects.exists())

    def test_nuevo_ciclo_no_hereda_seguimiento_anterior(self):
        marcar_no_interesado(**self.kwargs_accion())
        nuevo = self.registrar_mantenimiento(
            fecha=date(2027, 1, 1),
            kilometraje=15000,
        )

        alerta = self.alerta_actual()
        resultado = superponer_seguimientos(
            (alerta,), hoy=self.HOY, ahora=self.ahora
        )[0]

        self.assertEqual(alerta.ultimo_mantenimiento, nuevo)
        self.assertEqual(
            resultado.estado_seguimiento,
            SeguimientoMantenimiento.Estado.PENDIENTE,
        )
        self.assertIsNone(resultado.seguimiento)
        self.assertTrue(resultado.es_accionable)

    def test_nuevo_propietario_no_hereda_contacto_y_whatsapp_usa_sus_datos(self):
        marcar_contactado(**self.kwargs_accion())
        martin = Cliente.objects.create(
            nombre="Martín",
            telefono="261 444-2222",
        )
        self.moto.cliente = martin
        self.moto.save()

        alerta = self.alerta_actual()
        resultado = superponer_seguimientos(
            (alerta,), hoy=self.HOY, ahora=self.ahora
        )[0]

        self.assertEqual(
            resultado.estado_seguimiento,
            SeguimientoMantenimiento.Estado.PENDIENTE,
        )
        self.assertIsNone(resultado.seguimiento)
        self.assertIn("5492614442222", resultado.whatsapp_url)
        mensaje = parse_qs(urlparse(resultado.whatsapp_url).query)["text"][0]
        self.assertIn("Hola Martín", mensaje)
        self.assertEqual(
            SeguimientoMantenimiento.objects.get().cliente,
            self.carlos,
        )

    def test_cancelar_ultimo_servicio_recupera_seguimiento_del_ciclo_anterior(self):
        marcar_contactado(**self.kwargs_accion())
        nuevo = self.registrar_mantenimiento(
            fecha=date(2027, 1, 1),
            kilometraje=15000,
        )
        marcar_no_interesado(**self.kwargs_accion(base=nuevo))

        nuevo.servicio.estado = Servicio.Estado.CANCELADO
        nuevo.servicio.save(update_fields=("estado", "actualizado_en"))
        alerta = self.alerta_actual()
        resultado = superponer_seguimientos(
            (alerta,), hoy=self.HOY, ahora=self.ahora
        )[0]

        self.assertEqual(alerta.ultimo_mantenimiento, self.base)
        self.assertEqual(
            resultado.estado_seguimiento,
            SeguimientoMantenimiento.Estado.CONTACTADO,
        )
        self.assertTrue(resultado.es_accionable)

    def test_cambio_de_regla_oculta_y_reutiliza_el_mismo_seguimiento(self):
        marcar_contactado(**self.kwargs_accion())
        self.tipo.intervalo_km = 50000
        self.tipo.save()

        sin_alerta = obtener_resumen_seguimientos(
            hoy=self.HOY,
            ahora=self.ahora,
        )
        self.assertFalse(sin_alerta.alertas)
        self.assertEqual(SeguimientoMantenimiento.objects.count(), 1)

        self.tipo.intervalo_km = 5000
        self.tipo.save()
        nuevamente = obtener_resumen_seguimientos(
            hoy=self.HOY,
            ahora=self.ahora,
        )

        self.assertEqual(
            nuevamente.alertas[0].estado_seguimiento,
            SeguimientoMantenimiento.Estado.CONTACTADO,
        )
        self.assertEqual(SeguimientoMantenimiento.objects.count(), 1)

    def test_mutacion_revalida_moto_cliente_tipo_y_alerta(self):
        casos = ("moto", "cliente", "tipo", "recordatorio")
        for caso in casos:
            with self.subTest(caso=caso):
                if caso == "moto":
                    self.moto.activo = False
                    self.moto.save()
                elif caso == "cliente":
                    self.carlos.activo = False
                    self.carlos.save()
                elif caso == "tipo":
                    self.tipo.activo = False
                    self.tipo.save()
                else:
                    self.tipo.genera_recordatorio = False
                    self.tipo.save()

                with self.assertRaises(AlertaNoOperativa):
                    marcar_contactado(**self.kwargs_accion())
                self.assertFalse(SeguimientoMantenimiento.objects.exists())

                self.moto.activo = True
                self.moto.save()
                self.carlos.activo = True
                self.carlos.save()
                self.tipo.activo = True
                self.tipo.genera_recordatorio = True
                self.tipo.save()


class WhatsAppTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = Cliente.objects.create(
            nombre="José",
            telefono="+54 9 261 555-1000",
        )
        cls.moto = Moto.objects.create(
            cliente=cls.cliente,
            marca="Honda & Sons",
            modelo="Tornado XR250",
            kilometraje_actual=20000,
        )
        cls.tipo = TipoMantenimiento.objects.get(nombre="Cambio de aceite")
        cls.tipo.activo = True
        cls.tipo.genera_recordatorio = True
        cls.tipo.intervalo_km = 5000
        cls.tipo.aviso_km = 500
        cls.tipo.save()
        servicio = Servicio.objects.create(
            moto=cls.moto,
            fecha=date(2026, 1, 1),
            kilometraje=10000,
        )
        MantenimientoRealizado.objects.create(
            servicio=servicio,
            tipo_mantenimiento=cls.tipo,
        )

    def alerta(self):
        return construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2027, 1, 1),
        )[0]

    @override_settings(WHATSAPP_DEFAULT_COUNTRY_CODE="549")
    def test_normaliza_formatos_sin_modificar_el_valor_original(self):
        casos = (
            ("+54 9 261 555-1000", "5492615551000"),
            ("00 54 9 261 555-1000", "5492615551000"),
            ("261 555 1000", "5492615551000"),
            ("0261-555-1000", "5492615551000"),
            ("5492615551000", "5492615551000"),
            ("", None),
            ("sin teléfono", None),
        )

        for original, esperado in casos:
            with self.subTest(original=original):
                self.assertEqual(normalizar_numero_whatsapp(original), esperado)

        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.telefono, "+54 9 261 555-1000")

    @override_settings(TALLER_NOMBRE="Motos & Más")
    def test_url_codifica_mensaje_con_acentos_espacios_y_caracteres(self):
        alerta = self.alerta()

        url = construir_url_whatsapp(alerta)
        parsed = urlparse(url)
        mensaje = parse_qs(parsed.query)["text"][0]

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "wa.me")
        self.assertEqual(parsed.path, "/5492615551000")
        self.assertIn("Hola José, ¿cómo estás?", mensaje)
        self.assertIn("Motos & Más", mensaje)
        self.assertIn("Honda & Sons Tornado XR250", mensaje)
        self.assertIn("15.000 km", mensaje)
        self.assertIn("%C2%BF", url)
        self.assertIn("%26", url)

    @override_settings(TALLER_NOMBRE="")
    def test_nombre_vacio_se_omite_naturalmente(self):
        mensaje = construir_mensaje_whatsapp(self.alerta())

        self.assertNotIn("Te contactamos desde", mensaje)
        self.assertNotIn("None", mensaje)

    def test_telefono_invalido_no_genera_url(self):
        self.cliente.telefono = ""
        self.cliente.save()

        self.assertIsNone(construir_url_whatsapp(self.alerta()))
