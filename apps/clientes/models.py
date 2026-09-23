import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Value
from django.db.models.functions import Replace


def normalizar_espacios(valor):
    return " ".join((valor or "").split())


def normalizar_telefono_busqueda(valor):
    return re.sub(r"[\s()+.\-]", "", valor or "")


def expresion_telefono_normalizado(campo):
    expresion = campo
    for caracter in (" ", "-", "(", ")", "+", "."):
        expresion = Replace(expresion, Value(caracter), Value(""))
    return expresion


class ClienteQuerySet(models.QuerySet):
    def buscar(self, termino):
        termino = (termino or "").strip()
        if not termino:
            return self

        queryset = self
        if any(caracter.isdigit() for caracter in termino):
            queryset = queryset.annotate(
                telefono_busqueda=expresion_telefono_normalizado(F("telefono"))
            )

        filtros = Q()
        for parte in termino.split():
            filtro_parte = (
                Q(nombre__icontains=parte)
                | Q(apellido__icontains=parte)
                | Q(telefono__icontains=parte)
                | Q(email__icontains=parte)
            )
            if any(caracter.isdigit() for caracter in parte):
                telefono = normalizar_telefono_busqueda(parte)
                if telefono:
                    filtro_parte |= Q(telefono_busqueda__icontains=telefono)
            filtros &= filtro_parte

        return queryset.filter(filtros)


class Cliente(models.Model):
    nombre = models.CharField("nombre", max_length=100)
    apellido = models.CharField("apellido", max_length=100, blank=True)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    email = models.EmailField("email", blank=True)
    direccion = models.CharField("dirección", max_length=255, blank=True)
    observaciones = models.TextField("observaciones", blank=True)
    activo = models.BooleanField("activo", default=True)
    creado_en = models.DateTimeField("creado el", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado el", auto_now=True)

    objects = ClienteQuerySet.as_manager()

    class Meta:
        ordering = ("apellido", "nombre", "pk")
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    @property
    def nombre_completo(self):
        return " ".join(parte for parte in (self.nombre, self.apellido) if parte)

    def clean(self):
        super().clean()
        nombre_original = self.nombre
        self.nombre = normalizar_espacios(self.nombre)
        self.apellido = normalizar_espacios(self.apellido)
        self.telefono = normalizar_espacios(self.telefono)
        self.email = (self.email or "").strip()
        self.direccion = normalizar_espacios(self.direccion)

        if nombre_original and not self.nombre:
            raise ValidationError({"nombre": "Ingresá el nombre del cliente."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_completo
