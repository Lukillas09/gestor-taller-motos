import re
from dataclasses import dataclass

from django.conf import settings


FORMATO_TELEFONO = re.compile(r"^\+?[\d\s().-]+$")


@dataclass(frozen=True, slots=True)
class ContactoCliente:
    telefono_original: str
    telefono_tel: str | None
    whatsapp_url: str | None

    @property
    def puede_llamar(self):
        return self.telefono_tel is not None

    @property
    def puede_whatsapp(self):
        return self.whatsapp_url is not None

    @property
    def disponible(self):
        return self.puede_llamar or self.puede_whatsapp


def _telefono_con_formato_valido(telefono):
    original = str(telefono or "").strip()
    if not original or FORMATO_TELEFONO.fullmatch(original) is None:
        return None
    return original


def normalizar_telefono_tel(telefono):
    original = _telefono_con_formato_valido(telefono)
    if original is None:
        return None

    digitos = re.sub(r"\D", "", original)
    if not 6 <= len(digitos) <= 15:
        return None
    return f"+{digitos}" if original.startswith("+") else digitos


def normalizar_numero_whatsapp(telefono, *, prefijo_pais=None):
    original = _telefono_con_formato_valido(telefono)
    if original is None:
        return None

    digitos = re.sub(r"\D", "", original)
    prefijo = re.sub(
        r"\D",
        "",
        str(
            settings.WHATSAPP_DEFAULT_COUNTRY_CODE
            if prefijo_pais is None
            else prefijo_pais
        ),
    )

    if digitos.startswith("00"):
        numero = digitos[2:]
    elif original.startswith("+"):
        numero = digitos
    else:
        numero_local = digitos.lstrip("0")
        if prefijo and not numero_local.startswith(prefijo):
            numero = f"{prefijo}{numero_local}"
        else:
            numero = numero_local

    if not numero or numero.startswith("0") or not 8 <= len(numero) <= 15:
        return None
    return numero


def construir_url_whatsapp_contacto(telefono):
    numero = normalizar_numero_whatsapp(telefono)
    if numero is None:
        return None
    return f"https://wa.me/{numero}"


def obtener_contacto_cliente(cliente):
    telefono = str(getattr(cliente, "telefono", "") or "").strip()
    return ContactoCliente(
        telefono_original=telefono,
        telefono_tel=normalizar_telefono_tel(telefono),
        whatsapp_url=construir_url_whatsapp_contacto(telefono),
    )
