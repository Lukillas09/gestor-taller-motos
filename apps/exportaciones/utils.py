from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone


PREFIJOS_FORMULA = ("=", "+", "-", "@", "\t", "\r", "\n")


def texto_seguro_planilla(valor):
    """Representa texto controlado por usuarios sin permitir fórmulas."""
    texto = "" if valor is None else str(valor)
    if texto.startswith(PREFIJOS_FORMULA):
        return f"'{texto}"
    return texto


def safe_csv_text(valor):
    return texto_seguro_planilla(valor)


def safe_excel_text(valor):
    return texto_seguro_planilla(valor)


def datetime_local_naive(valor):
    if valor is None:
        return None
    if timezone.is_aware(valor):
        valor = timezone.localtime(valor)
    return valor.replace(tzinfo=None)


def valor_csv(valor):
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, datetime):
        return datetime_local_naive(valor).strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if isinstance(valor, Decimal):
        return format(valor, "f").replace(".", ",")
    if isinstance(valor, str):
        return safe_csv_text(valor)
    return valor


def valor_excel(valor):
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, datetime):
        return datetime_local_naive(valor)
    if isinstance(valor, str):
        return safe_excel_text(valor)
    return valor


def momento_local(momento=None):
    momento = momento or timezone.now()
    if timezone.is_aware(momento):
        return timezone.localtime(momento)
    return momento


def nombre_csv(slug, *, momento=None):
    return f"{slug}_{momento_local(momento):%Y-%m-%d}.csv"


def nombre_excel(*, momento=None):
    return f"motoservice_exportacion_{momento_local(momento):%Y-%m-%d_%H%M%S}.xlsx"
