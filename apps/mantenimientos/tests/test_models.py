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

    def test_catalogo_existente_conserva_recordatorios_desactivados(self):
        tipos = TipoMantenimiento.objects.filter(nombre__in=CATALOGO_ESPERADO)

        self.assertEqual(tipos.count(), 11)
        for tipo in tipos:
            with self.subTest(tipo=tipo.nombre):
                self.assertFalse(tipo.genera_recordatorio)
                self.assertIsNone(tipo.intervalo_meses)
                self.assertIsNone(tipo.intervalo_km)
                self.assertEqual(tipo.aviso_dias, 30)
                self.assertEqual(tipo.aviso_km, 0)

    def test_recordatorio_activo_requiere_algun_intervalo(self):
        with self.assertRaises(ValidationError) as contexto:
            TipoMantenimiento.objects.create(
                nombre="Ajuste sin regla",
                genera_recordatorio=True,
            )

        self.assertIn("genera_recordatorio", contexto.exception.message_dict)

    def test_intervalos_y_avisos_no_admiten_valores_invalidos(self):
        casos = (
            {"intervalo_meses": 0},
            {"intervalo_meses": -1},
            {"intervalo_km": 0},
            {"intervalo_km": -1},
            {"aviso_dias": -1},
            {"aviso_km": -1},
        )

        for indice, valores in enumerate(casos):
            with self.subTest(valores=valores), self.assertRaises(ValidationError):
                TipoMantenimiento.objects.create(
                    nombre=f"Regla inválida {indice}",
                    **valores,
                )

    def test_admite_reglas_por_meses_km_o_ambos(self):
        casos = (
            {"intervalo_meses": 12},
            {"intervalo_km": 6000},
            {"intervalo_meses": 12, "intervalo_km": 6000},
        )

        for indice, intervalos in enumerate(casos):
            with self.subTest(intervalos=intervalos):
                tipo = TipoMantenimiento.objects.create(
                    nombre=f"Regla válida {indice}",
                    genera_recordatorio=True,
                    **intervalos,
                )
                self.assertTrue(tipo.genera_recordatorio)

    def test_recordatorio_desactivado_puede_conservar_intervalos(self):
        tipo = TipoMantenimiento.objects.create(
            nombre="Regla pausada",
            genera_recordatorio=False,
            intervalo_meses=12,
            intervalo_km=6000,
        )

        self.assertEqual(tipo.intervalo_meses, 12)
        self.assertEqual(tipo.intervalo_km, 6000)

    def test_base_de_datos_protege_configuracion_invalida(self):
        tipo = TipoMantenimiento.objects.create(nombre="Regla protegida")

        with self.assertRaises(IntegrityError), transaction.atomic():
            TipoMantenimiento.objects.filter(pk=tipo.pk).update(
                genera_recordatorio=True,
                intervalo_meses=None,
                intervalo_km=None,
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            TipoMantenimiento.objects.filter(pk=tipo.pk).update(
                intervalo_meses=0,
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            TipoMantenimiento.objects.filter(pk=tipo.pk).update(
                aviso_km=-1,
            )


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
