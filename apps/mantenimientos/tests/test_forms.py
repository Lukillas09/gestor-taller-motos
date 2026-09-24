from django.test import TestCase

from apps.mantenimientos.forms import TipoMantenimientoForm


class TipoMantenimientoFormTests(TestCase):
    def datos(self, **cambios):
        datos = {
            "nombre": "Regulación de válvulas",
            "descripcion": "Control periódico",
            "activo": "on",
            "genera_recordatorio": "on",
            "intervalo_meses": "12",
            "intervalo_km": "",
            "aviso_dias": "30",
            "aviso_km": "0",
        }
        datos.update(cambios)
        return datos

    def test_rechaza_recordatorio_sin_intervalos(self):
        form = TipoMantenimientoForm(
            self.datos(intervalo_meses="", intervalo_km="")
        )

        self.assertFalse(form.is_valid())
        self.assertIn("genera_recordatorio", form.errors)

    def test_admite_regla_solo_por_meses(self):
        form = TipoMantenimientoForm(self.datos())

        self.assertTrue(form.is_valid(), form.errors)

    def test_admite_regla_solo_por_kilometros(self):
        form = TipoMantenimientoForm(
            self.datos(intervalo_meses="", intervalo_km="6000")
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_rechaza_intervalos_y_avisos_negativos(self):
        casos = (
            ("intervalo_meses", "0"),
            ("intervalo_km", "0"),
            ("aviso_dias", "-1"),
            ("aviso_km", "-1"),
        )

        for campo, valor in casos:
            with self.subTest(campo=campo):
                form = TipoMantenimientoForm(self.datos(**{campo: valor}))
                self.assertFalse(form.is_valid())
                self.assertIn(campo, form.errors)

    def test_permite_desactivar_recordatorio_sin_borrar_intervalos(self):
        form = TipoMantenimientoForm(
            self.datos(genera_recordatorio="", intervalo_km="6000")
        )

        self.assertTrue(form.is_valid(), form.errors)
        tipo = form.save()
        self.assertFalse(tipo.genera_recordatorio)
        self.assertEqual(tipo.intervalo_meses, 12)
        self.assertEqual(tipo.intervalo_km, 6000)
