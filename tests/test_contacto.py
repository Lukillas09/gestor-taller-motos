from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings

from apps.core.contacto import (
    construir_url_whatsapp_contacto,
    normalizar_numero_whatsapp,
    normalizar_telefono_tel,
    obtener_contacto_cliente,
)
from apps.notificaciones.services import (
    normalizar_numero_whatsapp as normalizar_numero_seguimiento,
)


class ContactoClienteTests(SimpleTestCase):
    def test_normaliza_telefono_para_tel_sin_modificar_el_original(self):
        casos = (
            ("+54 9 260 123-4567", "+5492601234567"),
            ("54 9 260 123-4567", "5492601234567"),
            ("(0260) 123-4567", "02601234567"),
            ("260.123.4567", "2601234567"),
            ("", None),
            (None, None),
            ("260 123 ABC", None),
            ("++54 9 260 1234567", None),
            ("12345", None),
        )

        for original, esperado in casos:
            with self.subTest(original=original):
                self.assertEqual(normalizar_telefono_tel(original), esperado)

        cliente = SimpleNamespace(telefono="+54 9 260 123-4567")
        obtener_contacto_cliente(cliente)
        self.assertEqual(cliente.telefono, "+54 9 260 123-4567")

    @override_settings(WHATSAPP_DEFAULT_COUNTRY_CODE="549")
    def test_contacto_general_reutiliza_normalizacion_y_no_agrega_mensaje(self):
        self.assertIs(
            normalizar_numero_whatsapp,
            normalizar_numero_seguimiento,
        )
        self.assertEqual(
            construir_url_whatsapp_contacto("260 123-4567"),
            "https://wa.me/5492601234567",
        )
        self.assertNotIn("?", construir_url_whatsapp_contacto("260 123-4567"))

    def test_whatsapp_vacio_o_invalido_no_genera_url(self):
        for telefono in ("", None, "sin teléfono", "260 123 ABC"):
            with self.subTest(telefono=telefono):
                self.assertIsNone(construir_url_whatsapp_contacto(telefono))

    @override_settings(WHATSAPP_DEFAULT_COUNTRY_CODE="")
    def test_llamada_puede_seguir_disponible_sin_whatsapp(self):
        contacto = obtener_contacto_cliente(
            SimpleNamespace(telefono="123-4567")
        )

        self.assertTrue(contacto.puede_llamar)
        self.assertFalse(contacto.puede_whatsapp)
        self.assertEqual(contacto.telefono_tel, "1234567")
