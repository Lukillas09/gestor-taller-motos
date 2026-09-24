from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def miles(valor):
    if valor is None or valor == "":
        return ""
    try:
        return f"{int(valor):,}".replace(",", ".")
    except (TypeError, ValueError):
        return valor


@register.filter
def dinero(valor):
    if valor is None or valor == "":
        return ""
    try:
        numero = Decimal(str(valor))
        formato = f"{numero:,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return valor
    formato = formato.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"$ {formato}"


@register.filter
def estado_badge(estado):
    return {
        "ABIERTO": "text-bg-primary",
        "FINALIZADO": "text-bg-success",
        "CANCELADO": "text-bg-secondary",
    }.get(estado, "text-bg-light")


@register.filter
def mantenimiento_badge(estado):
    valor = getattr(estado, "value", estado)
    return {
        "VENCIDO": "text-bg-danger",
        "PROXIMO": "text-bg-warning",
        "AL_DIA": "text-bg-success",
        "SIN_REGISTRO": "text-bg-secondary",
        "DATOS_INSUFICIENTES": "text-bg-secondary",
    }.get(valor, "text-bg-light")


@register.filter
def mantenimiento_tono(estado):
    valor = getattr(estado, "value", estado)
    return {
        "VENCIDO": "danger",
        "PROXIMO": "warning",
        "AL_DIA": "success",
        "SIN_REGISTRO": "secondary",
        "DATOS_INSUFICIENTES": "secondary",
    }.get(valor, "secondary")
