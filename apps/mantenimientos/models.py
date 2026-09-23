from django.core.exceptions import ValidationError
from django.db import models

from apps.clientes.models import normalizar_espacios


class TipoMantenimiento(models.Model):
    nombre = models.CharField("nombre", max_length=100, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    activo = models.BooleanField("activo", default=True)
    creado_en = models.DateTimeField("creado el", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado el", auto_now=True)

    class Meta:
        ordering = ("nombre", "pk")
        verbose_name = "tipo de mantenimiento"
        verbose_name_plural = "tipos de mantenimiento"

    def clean(self):
        super().clean()
        nombre_original = self.nombre
        self.nombre = normalizar_espacios(self.nombre)
        self.descripcion = (self.descripcion or "").strip()
        if nombre_original and not self.nombre:
            raise ValidationError({"nombre": "Ingresá el nombre del mantenimiento."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class MantenimientoRealizado(models.Model):
    servicio = models.ForeignKey(
        "servicios.Servicio",
        on_delete=models.CASCADE,
        related_name="mantenimientos_realizados",
        verbose_name="servicio",
    )
    tipo_mantenimiento = models.ForeignKey(
        TipoMantenimiento,
        on_delete=models.PROTECT,
        related_name="realizaciones",
        verbose_name="tipo de mantenimiento",
    )
    observaciones = models.TextField("observaciones", blank=True)
    creado_en = models.DateTimeField("creado el", auto_now_add=True)

    class Meta:
        ordering = ("tipo_mantenimiento__nombre", "pk")
        verbose_name = "mantenimiento realizado"
        verbose_name_plural = "mantenimientos realizados"
        constraints = (
            models.UniqueConstraint(
                fields=("servicio", "tipo_mantenimiento"),
                name="servicio_tipo_mantenimiento_unico",
            ),
        )

    def __str__(self):
        patente = self.servicio.moto.patente or "Sin patente"
        return f"{self.tipo_mantenimiento} — {patente}"
