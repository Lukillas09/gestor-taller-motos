from datetime import date

from django.test import TestCase

from apps.clientes.models import Cliente
from apps.mantenimientos.models import MantenimientoRealizado, TipoMantenimiento
from apps.mantenimientos.services import (
    EstadoMantenimiento,
    calcular_estado_mantenimiento,
    construir_estados,
    obtener_resumen_alertas,
    sumar_meses,
)
from apps.motos.models import Moto
from apps.servicios.models import Servicio


class CalculoMantenimientoTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(
            nombre="Carlos",
            apellido="González",
        )
        self.moto = Moto.objects.create(
            cliente=self.cliente,
            patente="AF123XY",
            marca="Honda",
            modelo="Tornado",
            kilometraje_actual=32000,
        )
        self.tipo = TipoMantenimiento.objects.get(nombre="Cambio de aceite")

    def configurar(self, tipo=None, **cambios):
        tipo = tipo or self.tipo
        valores = {
            "activo": True,
            "genera_recordatorio": True,
            "intervalo_meses": None,
            "intervalo_km": None,
            "aviso_dias": 30,
            "aviso_km": 0,
        }
        valores.update(cambios)
        for campo, valor in valores.items():
            setattr(tipo, campo, valor)
        tipo.save()
        return tipo

    def registrar(
        self,
        fecha,
        kilometraje,
        *,
        estado=Servicio.Estado.FINALIZADO,
        tipo=None,
        moto=None,
    ):
        moto = moto or self.moto
        servicio = Servicio.objects.create(
            moto=moto,
            fecha=fecha,
            kilometraje=kilometraje,
            estado=estado,
        )
        return MantenimientoRealizado.objects.create(
            servicio=servicio,
            tipo_mantenimiento=tipo or self.tipo,
        )

    def test_suma_meses_respeta_calendario(self):
        casos = (
            (date(2026, 9, 23), 12, date(2027, 9, 23)),
            (date(2026, 1, 31), 1, date(2026, 2, 28)),
            (date(2024, 1, 31), 1, date(2024, 2, 29)),
            (date(2024, 2, 29), 12, date(2025, 2, 28)),
        )

        for inicio, meses, esperado in casos:
            with self.subTest(inicio=inicio, meses=meses):
                self.assertEqual(sumar_meses(inicio, meses), esperado)

    def test_tipo_no_configurado_tiene_estado_explicito(self):
        resultado = calcular_estado_mantenimiento(
            self.moto,
            self.tipo,
            hoy=date(2026, 1, 1),
        )

        self.assertEqual(resultado.estado, EstadoMantenimiento.NO_CONFIGURADO)

    def test_regla_sin_mantenimiento_devuelve_sin_registro(self):
        self.configurar(intervalo_meses=12)

        resultado = calcular_estado_mantenimiento(
            self.moto,
            self.tipo,
            hoy=date(2026, 1, 1),
        )

        self.assertEqual(resultado.estado, EstadoMantenimiento.SIN_REGISTRO)

    def test_estados_por_fecha_son_deterministas(self):
        self.configurar(intervalo_meses=12, aviso_dias=30)
        ultimo = self.registrar(date(2026, 1, 1), 30000)
        casos = (
            (date(2026, 6, 1), EstadoMantenimiento.AL_DIA),
            (date(2026, 12, 10), EstadoMantenimiento.PROXIMO),
            (date(2027, 1, 1), EstadoMantenimiento.VENCIDO),
        )

        for hoy, esperado in casos:
            with self.subTest(hoy=hoy):
                resultado = calcular_estado_mantenimiento(
                    self.moto,
                    self.tipo,
                    ultimo,
                    hoy=hoy,
                )
                self.assertEqual(resultado.estado, esperado)
                self.assertEqual(resultado.proxima_fecha, date(2027, 1, 1))

    def test_fecha_exacta_esta_vencida_y_conserva_motivo(self):
        self.configurar(intervalo_meses=12, aviso_dias=30)
        ultimo = self.registrar(date(2026, 1, 1), 30000)

        resultado = calcular_estado_mantenimiento(
            self.moto,
            self.tipo,
            ultimo,
            hoy=date(2027, 1, 1),
        )

        self.assertEqual(resultado.estado, EstadoMantenimiento.VENCIDO)
        self.assertTrue(resultado.vencido_por_fecha)
        self.assertEqual(resultado.dias_restantes, 0)

    def test_estados_por_kilometraje(self):
        self.configurar(intervalo_km=6000, aviso_km=500)
        ultimo = self.registrar(date(2026, 1, 1), 30000)
        casos = (
            (32000, EstadoMantenimiento.AL_DIA),
            (35600, EstadoMantenimiento.PROXIMO),
            (36000, EstadoMantenimiento.VENCIDO),
            (40000, EstadoMantenimiento.VENCIDO),
        )

        for kilometraje, esperado in casos:
            with self.subTest(kilometraje=kilometraje):
                self.moto.kilometraje_actual = kilometraje
                resultado = calcular_estado_mantenimiento(
                    self.moto,
                    self.tipo,
                    ultimo,
                    hoy=date(2026, 6, 1),
                )
                self.assertEqual(resultado.estado, esperado)
                self.assertEqual(resultado.proximo_km, 36000)

    def test_km_exacto_esta_vencido_y_conserva_motivo(self):
        self.configurar(intervalo_km=6000, aviso_km=500)
        ultimo = self.registrar(date(2026, 1, 1), 30000)
        self.moto.kilometraje_actual = 36000

        resultado = calcular_estado_mantenimiento(
            self.moto,
            self.tipo,
            ultimo,
            hoy=date(2026, 6, 1),
        )

        self.assertEqual(resultado.estado, EstadoMantenimiento.VENCIDO)
        self.assertTrue(resultado.vencido_por_km)
        self.assertEqual(resultado.km_restantes, 0)

    def test_aviso_km_cero_no_crea_ventana_proxima(self):
        self.configurar(intervalo_km=6000, aviso_km=0)
        ultimo = self.registrar(date(2026, 1, 1), 30000)
        self.moto.kilometraje_actual = 35999

        resultado = calcular_estado_mantenimiento(
            self.moto,
            self.tipo,
            ultimo,
            hoy=date(2026, 6, 1),
        )

        self.assertEqual(resultado.estado, EstadoMantenimiento.AL_DIA)
        self.assertFalse(resultado.proximo_por_km)

    def test_fecha_y_km_aplican_el_limite_que_ocurra_primero(self):
        self.configurar(
            intervalo_meses=12,
            intervalo_km=6000,
            aviso_dias=30,
            aviso_km=500,
        )
        ultimo = self.registrar(date(2026, 1, 1), 30000)
        casos = (
            (date(2026, 6, 1), 36000, EstadoMantenimiento.VENCIDO),
            (date(2026, 12, 10), 32000, EstadoMantenimiento.PROXIMO),
            (date(2027, 1, 1), 35600, EstadoMantenimiento.VENCIDO),
            (date(2026, 6, 1), 32000, EstadoMantenimiento.AL_DIA),
        )

        for hoy, kilometraje, esperado in casos:
            with self.subTest(hoy=hoy, kilometraje=kilometraje):
                self.moto.kilometraje_actual = kilometraje
                resultado = calcular_estado_mantenimiento(
                    self.moto,
                    self.tipo,
                    ultimo,
                    hoy=hoy,
                )
                self.assertEqual(resultado.estado, esperado)

    def test_regla_solo_km_sin_ultimo_km_tiene_datos_insuficientes(self):
        self.configurar(intervalo_km=5000)
        ultimo = self.registrar(date(2026, 1, 1), None)

        resultado = calcular_estado_mantenimiento(
            self.moto,
            self.tipo,
            ultimo,
            hoy=date(2026, 6, 1),
        )

        self.assertEqual(resultado.estado, EstadoMantenimiento.DATOS_INSUFICIENTES)
        self.assertIsNone(resultado.proximo_km)

    def test_fecha_valida_se_calcula_aunque_falte_kilometraje(self):
        self.configurar(intervalo_meses=12, intervalo_km=5000)
        ultimo = self.registrar(date(2026, 1, 1), None)

        resultado = calcular_estado_mantenimiento(
            self.moto,
            self.tipo,
            ultimo,
            hoy=date(2026, 6, 1),
        )

        self.assertEqual(resultado.estado, EstadoMantenimiento.AL_DIA)
        self.assertEqual(resultado.proxima_fecha, date(2027, 1, 1))
        self.assertIsNone(resultado.proximo_km)

    def test_no_toma_kilometraje_de_un_mantenimiento_anterior(self):
        self.configurar(intervalo_km=5000)
        self.registrar(date(2025, 1, 1), 10000)
        reciente = self.registrar(date(2026, 1, 1), None)

        resultado = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 6, 1),
        )[0]

        self.assertEqual(resultado.ultimo_mantenimiento, reciente)
        self.assertIsNone(resultado.ultimo_km)
        self.assertEqual(resultado.estado, EstadoMantenimiento.DATOS_INSUFICIENTES)

    def test_solo_servicios_finalizados_y_no_futuros_reinician_ciclo(self):
        self.configurar(intervalo_meses=12)
        valido = self.registrar(date(2025, 1, 1), 10000)
        self.registrar(
            date(2025, 6, 1),
            12000,
            estado=Servicio.Estado.ABIERTO,
        )
        self.registrar(
            date(2026, 1, 1),
            14000,
            estado=Servicio.Estado.CANCELADO,
        )
        self.registrar(date(2027, 1, 1), 16000)

        resultado = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 6, 1),
        )[0]

        self.assertEqual(resultado.ultimo_mantenimiento, valido)
        self.assertEqual(resultado.estado, EstadoMantenimiento.VENCIDO)

    def test_cancelar_el_mas_reciente_restaura_el_ciclo_anterior(self):
        self.configurar(intervalo_meses=12)
        antiguo = self.registrar(date(2025, 1, 1), 10000)
        reciente = self.registrar(date(2026, 1, 1), 15000)

        antes = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 6, 1),
        )[0]
        reciente.servicio.estado = Servicio.Estado.CANCELADO
        reciente.servicio.save(update_fields=("estado", "actualizado_en"))
        despues = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 6, 1),
        )[0]

        self.assertEqual(antes.ultimo_mantenimiento, reciente)
        self.assertEqual(antes.estado, EstadoMantenimiento.AL_DIA)
        self.assertEqual(despues.ultimo_mantenimiento, antiguo)
        self.assertEqual(despues.estado, EstadoMantenimiento.VENCIDO)

    def test_servicio_abierto_reinicia_ciclo_al_finalizarse(self):
        self.configurar(intervalo_meses=12)
        antiguo = self.registrar(date(2025, 1, 1), 10000)
        nuevo = self.registrar(
            date(2026, 12, 1),
            15000,
            estado=Servicio.Estado.ABIERTO,
        )

        antes = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 12, 15),
        )[0]
        nuevo.servicio.estado = Servicio.Estado.FINALIZADO
        nuevo.servicio.save(update_fields=("estado", "actualizado_en"))
        despues = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 12, 15),
        )[0]

        self.assertEqual(antes.ultimo_mantenimiento, antiguo)
        self.assertEqual(antes.estado, EstadoMantenimiento.VENCIDO)
        self.assertEqual(despues.ultimo_mantenimiento, nuevo)
        self.assertEqual(despues.estado, EstadoMantenimiento.AL_DIA)

    def test_ultimo_se_define_por_fecha_del_servicio(self):
        self.configurar(intervalo_meses=12)
        reciente = self.registrar(date(2026, 1, 1), 15000)
        self.registrar(date(2025, 1, 1), 10000)

        resultado = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 6, 1),
        )[0]

        self.assertEqual(resultado.ultimo_mantenimiento, reciente)

    def test_modificar_regla_recalcula_sin_tocar_historial(self):
        self.configurar(intervalo_meses=12)
        ultimo = self.registrar(date(2026, 1, 1), 30000)
        antes = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 8, 1),
        )[0]

        self.tipo.intervalo_meses = 6
        self.tipo.save()
        despues = construir_estados(
            (self.moto,),
            (self.tipo,),
            hoy=date(2026, 8, 1),
        )[0]

        self.assertEqual(antes.estado, EstadoMantenimiento.AL_DIA)
        self.assertEqual(despues.estado, EstadoMantenimiento.VENCIDO)
        self.assertEqual(despues.ultimo_mantenimiento, ultimo)

    def test_tipos_mantienen_ciclos_independientes(self):
        self.configurar(intervalo_meses=12)
        filtro = TipoMantenimiento.objects.get(nombre="Filtro de aire")
        self.configurar(filtro, intervalo_meses=6)
        aceite = self.registrar(date(2026, 1, 1), 30000)
        aire = self.registrar(
            date(2026, 5, 1),
            31000,
            tipo=filtro,
        )

        resultados = construir_estados(
            (self.moto,),
            (self.tipo, filtro),
            hoy=date(2026, 8, 1),
        )

        por_tipo = {
            resultado.tipo_mantenimiento.pk: resultado
            for resultado in resultados
        }
        self.assertEqual(por_tipo[self.tipo.pk].ultimo_mantenimiento, aceite)
        self.assertEqual(por_tipo[filtro.pk].ultimo_mantenimiento, aire)
        self.assertEqual(por_tipo[self.tipo.pk].proxima_fecha, date(2027, 1, 1))
        self.assertEqual(por_tipo[filtro.pk].proxima_fecha, date(2026, 11, 1))


class AlertasOperativasTests(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(nombre="Lucía")
        self.moto = Moto.objects.create(
            cliente=self.cliente,
            marca="Yamaha",
            modelo="FZ",
            kilometraje_actual=20000,
        )
        self.tipo = TipoMantenimiento.objects.get(nombre="Cambio de aceite")
        self.tipo.genera_recordatorio = True
        self.tipo.intervalo_km = 5000
        self.tipo.aviso_km = 500
        self.tipo.save()
        servicio = Servicio.objects.create(
            moto=self.moto,
            fecha=date(2025, 1, 1),
            kilometraje=10000,
        )
        self.realizado = MantenimientoRealizado.objects.create(
            servicio=servicio,
            tipo_mantenimiento=self.tipo,
        )

    def test_excluye_moto_archivada(self):
        Moto.objects.filter(pk=self.moto.pk).update(activo=False)

        self.assertFalse(obtener_resumen_alertas(hoy=date(2026, 1, 1)).alertas)

    def test_excluye_cliente_actual_archivado(self):
        Cliente.objects.filter(pk=self.cliente.pk).update(activo=False)

        self.assertFalse(obtener_resumen_alertas(hoy=date(2026, 1, 1)).alertas)

    def test_excluye_tipo_inactivo(self):
        TipoMantenimiento.objects.filter(pk=self.tipo.pk).update(activo=False)

        self.assertFalse(obtener_resumen_alertas(hoy=date(2026, 1, 1)).alertas)

    def test_excluye_recordatorio_desactivado_sin_borrar_historial(self):
        TipoMantenimiento.objects.filter(pk=self.tipo.pk).update(
            genera_recordatorio=False
        )

        resumen = obtener_resumen_alertas(hoy=date(2026, 1, 1))

        self.assertFalse(resumen.alertas)
        self.assertTrue(
            MantenimientoRealizado.objects.filter(pk=self.realizado.pk).exists()
        )

    def test_construye_resumen_en_tres_consultas_sin_n_mas_uno(self):
        for indice in range(4):
            moto = Moto.objects.create(
                cliente=self.cliente,
                marca="Honda",
                modelo=f"Wave {indice}",
                kilometraje_actual=20000,
            )
            servicio = Servicio.objects.create(
                moto=moto,
                fecha=date(2025, 1, 1),
                kilometraje=10000,
            )
            MantenimientoRealizado.objects.create(
                servicio=servicio,
                tipo_mantenimiento=self.tipo,
            )

        with self.assertNumQueries(3):
            resumen = obtener_resumen_alertas(hoy=date(2026, 1, 1))
            list(resumen.alertas)

        self.assertEqual(len(resumen.vencidos), 5)
