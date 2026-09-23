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
