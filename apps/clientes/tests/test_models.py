from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from apps.clientes.models import Cliente
from apps.motos.models import Moto


class ClienteModelTests(TestCase):
    def test_creacion_normaliza_nombre_y_representacion(self):
        cliente = Cliente.objects.create(
            nombre="  Carlos   Alberto ",
            apellido=" González  ",
            telefono=" 260   4123456 ",
        )

        self.assertEqual(cliente.nombre, "Carlos Alberto")
        self.assertEqual(cliente.apellido, "González")
        self.assertEqual(cliente.telefono, "260 4123456")
        self.assertEqual(str(cliente), "Carlos Alberto González")
        self.assertTrue(cliente.activo)

    def test_nombre_compuesto_solo_por_espacios_es_invalido(self):
        with self.assertRaises(ValidationError) as error:
            Cliente.objects.create(nombre="   ")

        self.assertIn("nombre", error.exception.message_dict)

    def test_cliente_puede_archivarse_sin_borrarse(self):
        cliente = Cliente.objects.create(nombre="Carlos")

        cliente.activo = False
        cliente.save(update_fields=("activo", "actualizado_en"))

        self.assertFalse(Cliente.objects.get(pk=cliente.pk).activo)

    def test_relacion_expone_motos_y_protege_cliente(self):
        cliente = Cliente.objects.create(nombre="Carlos")
        moto = Moto.objects.create(cliente=cliente, marca="Honda", modelo="Tornado")

        self.assertQuerySetEqual(cliente.motos.all(), [moto])
        with self.assertRaises(ProtectedError):
            cliente.delete()

    def test_busqueda_de_telefono_ignora_formato(self):
        cliente = Cliente.objects.create(
            nombre="Carlos", apellido="González", telefono="+54 9 260 4123456"
        )

        self.assertQuerySetEqual(Cliente.objects.buscar("2604"), [cliente])
        self.assertQuerySetEqual(Cliente.objects.buscar("Carlos González"), [cliente])
