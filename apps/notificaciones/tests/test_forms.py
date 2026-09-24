from datetime import date, datetime

from django.test import SimpleTestCase
from django.utils import timezone

from apps.notificaciones.forms import NotaForm, PosponerForm, TurnoForm


class PosponerFormTests(SimpleTestCase):
    def test_calcula_plazos_rapidos_desde_la_fecha_local(self):
        hoy = date(2027, 10, 1)

        for plazo, esperado in (
            ("7", date(2027, 10, 8)),
            ("15", date(2027, 10, 16)),
            ("30", date(2027, 10, 31)),
        ):
            with self.subTest(plazo=plazo):
                form = PosponerForm(
                    {"mantenimiento_base": 1, "plazo": plazo},
                    hoy=hoy,
                )
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["pospuesto_hasta"], esperado)

    def test_fecha_personalizada_debe_ser_futura(self):
        hoy = date(2027, 10, 1)

        for fecha in ("2027-09-30", "2027-10-01"):
            with self.subTest(fecha=fecha):
                form = PosponerForm(
                    {
                        "mantenimiento_base": 1,
                        "plazo": "personalizada",
                        "fecha_personalizada": fecha,
                    },
                    hoy=hoy,
                )
                self.assertFalse(form.is_valid())
                self.assertIn("fecha_personalizada", form.errors)

    def test_fecha_personalizada_futura_es_valida(self):
        form = PosponerForm(
            {
                "mantenimiento_base": 1,
                "plazo": "personalizada",
                "fecha_personalizada": "2027-10-10",
            },
            hoy=date(2027, 10, 1),
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["pospuesto_hasta"],
            date(2027, 10, 10),
        )


class TurnoFormTests(SimpleTestCase):
    def setUp(self):
        self.ahora = timezone.make_aware(datetime(2027, 10, 1, 10, 0))

    def test_turno_debe_ser_futuro_y_queda_timezone_aware(self):
        pasado = TurnoForm(
            {"mantenimiento_base": 1, "turno_para": "2027-10-01T09:59"},
            ahora=self.ahora,
        )
        futuro = TurnoForm(
            {"mantenimiento_base": 1, "turno_para": "2027-10-01T10:01"},
            ahora=self.ahora,
        )

        self.assertFalse(pasado.is_valid())
        self.assertTrue(futuro.is_valid(), futuro.errors)
        self.assertTrue(timezone.is_aware(futuro.cleaned_data["turno_para"]))

    def test_nota_requiere_texto(self):
        form = NotaForm({"mantenimiento_base": 1, "nota": ""})

        self.assertFalse(form.is_valid())
        self.assertIn("nota", form.errors)
