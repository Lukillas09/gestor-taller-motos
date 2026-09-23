from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.clientes.models import Cliente
from apps.motos.models import Moto
from apps.servicios.models import Servicio

from apps.mantenimientos.models import MantenimientoRealizado, TipoMantenimiento


CATALOGO_ESPERADO = {
    "Cambio de aceite",
    "Filtro de aceite",
    "Filtro de aire",
    "Bujías",
    "Pastillas de freno",
    "Líquido de freno",
    "Líquido refrigerante",
    "Cadena / transmisión",
    "Cubiertas",
    "Batería",
    "Service general",
}


class TipoMantenimientoTests(TestCase):
    def test_migracion_carga_catalogo_inicial(self):
        self.assertTrue(
            CATALOGO_ESPERADO.issubset(
                set(TipoMantenimiento.objects.values_list("nombre", flat=True))
            )
        )

    def test_normaliza_nombre_y_descripcion(self):
        tipo = TipoMantenimiento.objects.create(
            nombre="  Ajuste   de válvulas  ",
            descripcion="  Control completo  ",
        )

        self.assertEqual(tipo.nombre, "Ajuste de válvulas")
        self.assertEqual(tipo.descripcion, "Control completo")

    def test_nombre_no_puede_contener_solo_espacios(self):
        with self.assertRaises(ValidationError):
            TipoMantenimiento.objects.create(nombre="   ")


class MantenimientoRealizadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cliente = Cliente.objects.create(nombre="Carlos")
        moto = Moto.objects.create(cliente=cliente, marca="Honda", modelo="Wave")
        cls.servicio = Servicio.objects.create(moto=moto)
        cls.tipo = TipoMantenimiento.objects.get(nombre="Cambio de aceite")

    def test_no_admite_el_mismo_tipo_dos_veces_en_un_servicio(self):
        realizado = MantenimientoRealizado.objects.create(
            servicio=self.servicio,
            tipo_mantenimiento=self.tipo,
        )

        self.assertEqual(realizado.servicio, self.servicio)
        self.assertEqual(realizado.tipo_mantenimiento, self.tipo)
        self.assertEqual(str(realizado), "Cambio de aceite — Sin patente")

        with self.assertRaises(IntegrityError), transaction.atomic():
            MantenimientoRealizado.objects.create(
                servicio=self.servicio,
                tipo_mantenimiento=self.tipo,
            )

    def test_tipo_usado_esta_protegido(self):
        MantenimientoRealizado.objects.create(
            servicio=self.servicio,
            tipo_mantenimiento=self.tipo,
        )

        with self.assertRaises(ProtectedError):
            self.tipo.delete()
