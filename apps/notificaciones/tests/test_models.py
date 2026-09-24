from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.mantenimientos.models import MantenimientoRealizado, TipoMantenimiento
from apps.motos.models import Moto
from apps.notificaciones.models import (
    EventoSeguimientoMantenimiento,
    SeguimientoMantenimiento,
)
from apps.servicios.models import Servicio


class SeguimientoMantenimientoModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(username="juan")
        cls.cliente = Cliente.objects.create(nombre="Carlos", apellido="Pérez")
        cls.otro_cliente = Cliente.objects.create(nombre="Martín")
        cls.moto = Moto.objects.create(
            cliente=cls.cliente,
            marca="Honda",
            modelo="Tornado",
        )
        servicio = Servicio.objects.create(
            moto=cls.moto,
            fecha=date(2026, 1, 1),
            kilometraje=10000,
        )
        cls.tipo = TipoMantenimiento.objects.get(nombre="Cambio de aceite")
        cls.base = MantenimientoRealizado.objects.create(
            servicio=servicio,
            tipo_mantenimiento=cls.tipo,
        )

    def crear_seguimiento(self, **cambios):
        datos = {
            "mantenimiento_base": self.base,
            "cliente": self.cliente,
            "actualizado_por": self.usuario,
        }
        datos.update(cambios)
        return SeguimientoMantenimiento.objects.create(**datos)

    def test_estado_inicial_y_texto_representativo(self):
        seguimiento = self.crear_seguimiento()

        self.assertEqual(
            seguimiento.estado,
            SeguimientoMantenimiento.Estado.PENDIENTE,
        )
        self.assertEqual(
            str(seguimiento),
            "Cambio de aceite — Honda Tornado — Carlos Pérez",
        )

    def test_ciclo_y_cliente_son_unicos(self):
        self.crear_seguimiento()

        with self.assertRaises(ValidationError):
            self.crear_seguimiento()

        otro = self.crear_seguimiento(cliente=self.otro_cliente)
        self.assertEqual(otro.cliente, self.otro_cliente)

    def test_constraint_de_base_protege_unicidad(self):
        self.crear_seguimiento()
        with self.assertRaises(IntegrityError), transaction.atomic():
            SeguimientoMantenimiento.objects.bulk_create(
                [
                    SeguimientoMantenimiento(
                        mantenimiento_base=self.base,
                        cliente=self.cliente,
                    )
                ]
            )

    def test_pospuesto_y_turno_requieren_su_fecha(self):
        casos = (
            {"estado": SeguimientoMantenimiento.Estado.POSPUESTO},
            {"estado": SeguimientoMantenimiento.Estado.TURNO_ACORDADO},
            {
                "estado": SeguimientoMantenimiento.Estado.CONTACTADO,
                "pospuesto_hasta": date(2026, 2, 1),
            },
            {
                "estado": SeguimientoMantenimiento.Estado.PENDIENTE,
                "turno_para": timezone.now(),
            },
        )

        for valores in casos:
            with self.subTest(valores=valores), self.assertRaises(ValidationError):
                self.crear_seguimiento(**valores)

    def test_constraints_sql_protegen_fechas_de_estado(self):
        seguimiento = self.crear_seguimiento()

        with self.assertRaises(IntegrityError), transaction.atomic():
            SeguimientoMantenimiento.objects.filter(pk=seguimiento.pk).update(
                estado=SeguimientoMantenimiento.Estado.POSPUESTO,
                pospuesto_hasta=None,
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            SeguimientoMantenimiento.objects.filter(pk=seguimiento.pk).update(
                pospuesto_hasta=date(2026, 2, 1),
            )

    def test_base_y_cliente_estan_protegidos(self):
        seguimiento = self.crear_seguimiento(cliente=self.otro_cliente)

        with self.assertRaises(ProtectedError):
            self.base.delete()
        with self.assertRaises(ProtectedError):
            self.otro_cliente.delete()
        self.assertTrue(
            SeguimientoMantenimiento.objects.filter(pk=seguimiento.pk).exists()
        )

    def test_eventos_preservan_historial_y_usuario_es_opcional(self):
        seguimiento = self.crear_seguimiento()
        evento = EventoSeguimientoMantenimiento.objects.create(
            seguimiento=seguimiento,
            tipo_evento=EventoSeguimientoMantenimiento.Tipo.CONTACTADO,
            usuario=self.usuario,
            nota="Hablé con el cliente.",
        )

        self.usuario.delete()
        evento.refresh_from_db()
        self.assertIsNone(evento.usuario)
        self.assertEqual(evento.nota, "Hablé con el cliente.")
        self.assertTrue(str(evento).startswith("Contactado —"))

    def test_evento_se_elimina_con_su_seguimiento(self):
        seguimiento = self.crear_seguimiento()
        EventoSeguimientoMantenimiento.objects.create(
            seguimiento=seguimiento,
            tipo_evento=EventoSeguimientoMantenimiento.Tipo.NOTA,
            nota="Recordar por la tarde.",
        )

        seguimiento.delete()

        self.assertFalse(EventoSeguimientoMantenimiento.objects.exists())
