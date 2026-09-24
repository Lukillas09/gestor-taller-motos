from datetime import datetime

from django.test import SimpleTestCase

from apps.exportaciones.utils import (
    nombre_csv,
    nombre_excel,
    safe_csv_text,
    safe_excel_text,
)


class ExportacionUtilsTests(SimpleTestCase):
    def test_texto_peligroso_se_exporta_como_literal(self):
        for valor in ("=2+2", "+cmd", "-10", "@SUM(A1:A2)", "\t=2+2"):
            with self.subTest(valor=valor):
                self.assertEqual(safe_csv_text(valor), f"'{valor}")
                self.assertEqual(safe_excel_text(valor), f"'{valor}")

    def test_texto_normal_no_se_modifica(self):
        self.assertEqual(safe_csv_text("Lucía González"), "Lucía González")
        self.assertEqual(safe_excel_text("Honda Tornado"), "Honda Tornado")

    def test_nombres_de_archivo_no_incluyen_datos_del_usuario(self):
        momento = datetime(2026, 9, 24, 16, 30)

        self.assertEqual(nombre_csv("clientes", momento=momento), "clientes_2026-09-24.csv")
        self.assertEqual(
            nombre_excel(momento=momento),
            "motoservice_exportacion_2026-09-24_163000.xlsx",
        )
