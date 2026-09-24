from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from django.utils import timezone

from apps.motos.models import Moto
from apps.servicios.models import Servicio

from .models import MantenimientoRealizado, TipoMantenimiento


class EstadoMantenimiento(str, Enum):
    AL_DIA = "AL_DIA"
    PROXIMO = "PROXIMO"
    VENCIDO = "VENCIDO"
    SIN_REGISTRO = "SIN_REGISTRO"
    DATOS_INSUFICIENTES = "DATOS_INSUFICIENTES"
    NO_CONFIGURADO = "NO_CONFIGURADO"


ETIQUETAS_ESTADO = {
    EstadoMantenimiento.AL_DIA: "Al día",
    EstadoMantenimiento.PROXIMO: "Próximo",
    EstadoMantenimiento.VENCIDO: "Vencido",
    EstadoMantenimiento.SIN_REGISTRO: "Sin registro",
    EstadoMantenimiento.DATOS_INSUFICIENTES: "Datos insuficientes",
    EstadoMantenimiento.NO_CONFIGURADO: "No configurado",
}


@dataclass(frozen=True, slots=True)
class ResultadoMantenimiento:
    moto: Moto
    tipo_mantenimiento: TipoMantenimiento
    ultimo_mantenimiento: MantenimientoRealizado | None
    estado: EstadoMantenimiento
    ultima_fecha: date | None = None
    ultimo_km: int | None = None
    proxima_fecha: date | None = None
    proximo_km: int | None = None
    dias_restantes: int | None = None
    km_restantes: int | None = None
    vencido_por_fecha: bool = False
    vencido_por_km: bool = False
    proximo_por_fecha: bool = False
    proximo_por_km: bool = False

    @property
    def estado_label(self):
        return ETIQUETAS_ESTADO[self.estado]

    @property
    def dias_vencido(self):
        if self.dias_restantes is None or self.dias_restantes >= 0:
            return 0
        return -self.dias_restantes

    @property
    def km_excedidos(self):
        if self.km_restantes is None or self.km_restantes >= 0:
            return 0
        return -self.km_restantes


@dataclass(frozen=True, slots=True)
class ResumenAlertas:
    tipos_configurados: tuple[TipoMantenimiento, ...]
    alertas: tuple[ResultadoMantenimiento, ...]
    vencidos: tuple[ResultadoMantenimiento, ...]
    proximos: tuple[ResultadoMantenimiento, ...]

    @property
    def hay_reglas(self):
        return bool(self.tipos_configurados)


def sumar_meses(fecha, meses):
    if meses < 0:
        raise ValueError("La cantidad de meses no puede ser negativa.")
    indice_mes = fecha.month - 1 + meses
    anio = fecha.year + indice_mes // 12
    mes = indice_mes % 12 + 1
    dia = min(fecha.day, monthrange(anio, mes)[1])
    return fecha.replace(year=anio, month=mes, day=dia)


def calcular_estado_mantenimiento(moto, tipo_mantenimiento, ultimo=None, *, hoy=None):
    hoy = hoy or timezone.localdate()
    if not tipo_mantenimiento.activo or not tipo_mantenimiento.genera_recordatorio:
        return ResultadoMantenimiento(
            moto=moto,
            tipo_mantenimiento=tipo_mantenimiento,
            ultimo_mantenimiento=ultimo,
            estado=EstadoMantenimiento.NO_CONFIGURADO,
        )

    if ultimo is None:
        return ResultadoMantenimiento(
            moto=moto,
            tipo_mantenimiento=tipo_mantenimiento,
            ultimo_mantenimiento=None,
            estado=EstadoMantenimiento.SIN_REGISTRO,
        )

    ultima_fecha = ultimo.servicio.fecha
    ultimo_km = ultimo.servicio.kilometraje
    proxima_fecha = None
    proximo_km = None
    dias_restantes = None
    km_restantes = None
    vencido_por_fecha = False
    vencido_por_km = False
    proximo_por_fecha = False
    proximo_por_km = False
    dimension_calculable = False

    if tipo_mantenimiento.intervalo_meses is not None:
        dimension_calculable = True
        proxima_fecha = sumar_meses(
            ultima_fecha,
            tipo_mantenimiento.intervalo_meses,
        )
        dias_restantes = (proxima_fecha - hoy).days
        if hoy >= proxima_fecha:
            vencido_por_fecha = True
        elif (
            tipo_mantenimiento.aviso_dias > 0
            and hoy >= proxima_fecha - timedelta(days=tipo_mantenimiento.aviso_dias)
        ):
            proximo_por_fecha = True

    if tipo_mantenimiento.intervalo_km is not None and ultimo_km is not None:
        proximo_km = ultimo_km + tipo_mantenimiento.intervalo_km
        if moto.kilometraje_actual is not None:
            dimension_calculable = True
            km_restantes = proximo_km - moto.kilometraje_actual
            if moto.kilometraje_actual >= proximo_km:
                vencido_por_km = True
            elif (
                tipo_mantenimiento.aviso_km > 0
                and moto.kilometraje_actual
                >= proximo_km - tipo_mantenimiento.aviso_km
            ):
                proximo_por_km = True

    if vencido_por_fecha or vencido_por_km:
        estado = EstadoMantenimiento.VENCIDO
    elif proximo_por_fecha or proximo_por_km:
        estado = EstadoMantenimiento.PROXIMO
    elif dimension_calculable:
        estado = EstadoMantenimiento.AL_DIA
    else:
        estado = EstadoMantenimiento.DATOS_INSUFICIENTES

    return ResultadoMantenimiento(
        moto=moto,
        tipo_mantenimiento=tipo_mantenimiento,
        ultimo_mantenimiento=ultimo,
        estado=estado,
        ultima_fecha=ultima_fecha,
        ultimo_km=ultimo_km,
        proxima_fecha=proxima_fecha,
        proximo_km=proximo_km,
        dias_restantes=dias_restantes,
        km_restantes=km_restantes,
        vencido_por_fecha=vencido_por_fecha,
        vencido_por_km=vencido_por_km,
        proximo_por_fecha=proximo_por_fecha,
        proximo_por_km=proximo_por_km,
    )


def obtener_ultimos_mantenimientos(motos, tipos_mantenimiento, *, hoy=None):
    hoy = hoy or timezone.localdate()
    motos_ids = [moto.pk for moto in motos]
    tipos_ids = [tipo.pk for tipo in tipos_mantenimiento]
    if not motos_ids or not tipos_ids:
        return {}

    realizados = (
        MantenimientoRealizado.objects.filter(
            servicio__moto_id__in=motos_ids,
            tipo_mantenimiento_id__in=tipos_ids,
            servicio__estado=Servicio.Estado.FINALIZADO,
            servicio__fecha__lte=hoy,
        )
        .select_related(
            "servicio",
            "servicio__moto",
            "servicio__cliente",
            "tipo_mantenimiento",
        )
        .order_by(
            "servicio__moto_id",
            "tipo_mantenimiento_id",
            "-servicio__fecha",
            "-servicio_id",
            "-pk",
        )
    )

    ultimos = {}
    for realizado in realizados:
        clave = (realizado.servicio.moto_id, realizado.tipo_mantenimiento_id)
        ultimos.setdefault(clave, realizado)
    return ultimos


def construir_estados(motos, tipos_mantenimiento, *, hoy=None):
    hoy = hoy or timezone.localdate()
    motos = tuple(motos)
    tipos_mantenimiento = tuple(tipos_mantenimiento)
    ultimos = obtener_ultimos_mantenimientos(
        motos,
        tipos_mantenimiento,
        hoy=hoy,
    )
    return tuple(
        calcular_estado_mantenimiento(
            moto,
            tipo,
            ultimos.get((moto.pk, tipo.pk)),
            hoy=hoy,
        )
        for moto in motos
        for tipo in tipos_mantenimiento
    )


def obtener_estados_moto(moto, *, hoy=None):
    tipos = tuple(
        TipoMantenimiento.objects.filter(
            activo=True,
            genera_recordatorio=True,
        ).order_by("nombre", "pk")
    )
    return construir_estados((moto,), tipos, hoy=hoy)


def _clave_urgencia(resultado):
    prioridad_estado = 0 if resultado.estado == EstadoMantenimiento.VENCIDO else 1
    usa_fecha = resultado.vencido_por_fecha or resultado.proximo_por_fecha
    if usa_fecha:
        prioridad_dimension = 0
        urgencia = (
            resultado.proxima_fecha.toordinal()
            if resultado.proxima_fecha
            else 0
        )
    else:
        prioridad_dimension = 1
        urgencia = resultado.km_restantes if resultado.km_restantes is not None else 0
    return (
        prioridad_estado,
        prioridad_dimension,
        urgencia,
        resultado.tipo_mantenimiento.nombre.casefold(),
        resultado.moto.pk,
    )


def obtener_resumen_alertas(*, hoy=None):
    hoy = hoy or timezone.localdate()
    tipos = tuple(
        TipoMantenimiento.objects.filter(
            activo=True,
            genera_recordatorio=True,
        ).order_by("nombre", "pk")
    )
    if not tipos:
        return ResumenAlertas((), (), (), ())

    motos = tuple(
        Moto.objects.filter(
            activo=True,
            cliente__activo=True,
        )
        .select_related("cliente")
        .order_by("marca", "modelo", "pk")
    )
    estados = construir_estados(motos, tipos, hoy=hoy)
    alertas = tuple(
        sorted(
            (
                estado
                for estado in estados
                if estado.estado
                in (EstadoMantenimiento.VENCIDO, EstadoMantenimiento.PROXIMO)
            ),
            key=_clave_urgencia,
        )
    )
    vencidos = tuple(
        alerta
        for alerta in alertas
        if alerta.estado == EstadoMantenimiento.VENCIDO
    )
    proximos = tuple(
        alerta
        for alerta in alertas
        if alerta.estado == EstadoMantenimiento.PROXIMO
    )
    return ResumenAlertas(tipos, alertas, vencidos, proximos)
