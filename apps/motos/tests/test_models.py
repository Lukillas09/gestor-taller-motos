from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.motos.models import Moto, normalizar_patente


class MotoModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = Cliente.objects.create(nombre="Carlos", apellido="González")

    def test_creacion_y_representacion_con_patente(self):
        moto = Moto.objects.create(
            cliente=self.cliente,
            patente="af-123 xy",
            marca="  Honda ",
            modelo=" Tornado   XR250 ",
        )

        self.assertEqual(moto.patente, "AF123XY")
        self.assertEqual(moto.marca, "Honda")
        self.assertEqual(moto.modelo, "Tornado XR250")
        self.assertEqual(str(moto), "Honda Tornado XR250 — AF123XY")

    def test_representacion_sin_patente(self):
        moto = Moto.objects.create(
            cliente=self.cliente, marca="Honda", modelo="CRF"
        )

        self.assertEqual(str(moto), "Honda CRF")

    def test_normalizacion_de_patente_esta_centralizada(self):
        self.assertEqual(normalizar_patente(" af-123 xy "), "AF123XY")
        self.assertIsNone(normalizar_patente(" -  - "))

    def test_patente_duplicada_es_invalida_despues_de_normalizar(self):
        Moto.objects.create(
            cliente=self.cliente,
            patente="AF123XY",
            marca="Honda",
            modelo="Tornado",
        )

        with self.assertRaises(ValidationError) as error:
            Moto.objects.create(
                cliente=self.cliente,
                patente="af-123-xy",
                marca="Yamaha",
                modelo="FZ",
            )

        self.assertIn("patente", error.exception.message_dict)

    def test_varias_motos_pueden_no_tener_patente(self):
        primera = Moto.objects.create(
            cliente=self.cliente, patente="", marca="Honda", modelo="CRF"
        )
        segunda = Moto.objects.create(
            cliente=self.cliente, patente=None, marca="Yamaha", modelo="YZ"
        )

        self.assertIsNone(primera.patente)
        self.assertIsNone(segunda.patente)

    def test_anio_actual_y_siguiente_son_validos(self):
        actual = timezone.localdate().year

        for anio in (actual, actual + 1):
            with self.subTest(anio=anio):
                moto = Moto(
                    cliente=self.cliente,
                    marca="Honda",
                    modelo="Wave",
                    anio=anio,
                )
                moto.full_clean()

    def test_anio_fuera_de_rango_es_invalido(self):
        for anio in (1899, timezone.localdate().year + 2):
            with self.subTest(anio=anio), self.assertRaises(ValidationError):
                Moto.objects.create(
                    cliente=self.cliente,
                    marca="Honda",
                    modelo="Wave",
                    anio=anio,
                )

    def test_kilometraje_y_cilindrada_no_aceptan_negativos(self):
        casos = (
            {"kilometraje_actual": -1},
            {"cilindrada_cc": -1},
        )

        for datos in casos:
            with self.subTest(datos=datos), self.assertRaises(ValidationError):
                Moto.objects.create(
                    cliente=self.cliente,
                    marca="Honda",
                    modelo="Wave",
                    **datos,
                )

    def test_cliente_es_obligatorio(self):
        moto = Moto(marca="Honda", modelo="Wave")

        with self.assertRaises(ValidationError) as error:
            moto.full_clean()

        self.assertIn("cliente", error.exception.message_dict)

    def test_busqueda_por_patente_y_telefono_del_cliente(self):
        self.cliente.telefono = "+54 9 260 4123456"
        self.cliente.save()
        moto = Moto.objects.create(
            cliente=self.cliente,
            patente="AF123XY",
            marca="Honda",
            modelo="Tornado",
        )

        self.assertQuerySetEqual(Moto.objects.buscar("af-123-xy"), [moto])
        self.assertQuerySetEqual(Moto.objects.buscar("2604"), [moto])
        self.assertQuerySetEqual(Moto.objects.buscar("Honda Tornado"), [moto])
