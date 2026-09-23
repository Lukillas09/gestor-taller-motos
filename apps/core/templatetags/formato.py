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
