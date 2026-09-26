from django import template

from apps.core.contacto import obtener_contacto_cliente


register = template.Library()


@register.inclusion_tag("shared/contacto_cliente.html")
def contacto_cliente(cliente, variante="compacto"):
    if variante not in {"compacto", "detalle"}:
        variante = "compacto"
    return {
        "cliente": cliente,
        "contacto": obtener_contacto_cliente(cliente),
        "variante": variante,
    }
