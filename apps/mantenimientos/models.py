from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.clientes.models import normalizar_espacios


class TipoMantenimiento(models.Model):
    nombre = models.CharField("nombre", max_length=100, unique=True)
    descripcion = models.TextField("descripción", blank=True)
    activo = models.BooleanField("activo", default=True)
    genera_recordatorio = models.BooleanField(
        "genera recordatorio",
        default=False,
    )
    intervalo_meses = models.PositiveSmallIntegerField(
        "intervalo en meses",
        blank=True,
        null=True,
        validators=(MinValueValidator(1),),
    )
    intervalo_km = models.PositiveIntegerField(
        "intervalo en kilómetros",
        blank=True,
        null=True,
        validators=(MinValueValidator(1),),
    )
    aviso_dias = models.PositiveSmallIntegerField(
        "aviso anticipado en días",
        default=30,
        validators=(MinValueValidator(0),),
    )
    aviso_km = models.PositiveIntegerField(
        "aviso anticipado en kilómetros",
        default=0,
        validators=(MinValueValidator(0),),
    )
    creado_en = models.DateTimeField("creado el", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado el", auto_now=True)

    class Meta:
        ordering = ("nombre", "pk")
        verbose_name = "tipo de mantenimiento"
        verbose_name_plural = "tipos de mantenimiento"
        constraints = (
            models.CheckConstraint(
                condition=Q(intervalo_meses__isnull=True)
                | Q(intervalo_meses__gte=1),
                name="tipo_intervalo_meses_positivo",
            ),
            models.CheckConstraint(
                condition=Q(intervalo_km__isnull=True) | Q(intervalo_km__gte=1),
                name="tipo_intervalo_km_positivo",
            ),
            models.CheckConstraint(
                condition=Q(aviso_dias__gte=0),
                name="tipo_aviso_dias_no_negativo",
            ),
            models.CheckConstraint(
                condition=Q(aviso_km__gte=0),
                name="tipo_aviso_km_no_negativo",
            ),
            models.CheckConstraint(
                condition=Q(genera_recordatorio=False)
                | Q(intervalo_meses__isnull=False)
                | Q(intervalo_km__isnull=False),
                name="tipo_recordatorio_con_intervalo",
            ),
        )

    def clean(self):
        super().clean()
        nombre_original = self.nombre
        self.nombre = normalizar_espacios(self.nombre)
        self.descripcion = (self.descripcion or "").strip()
        if nombre_original and not self.nombre:
            raise ValidationError({"nombre": "Ingresá el nombre del mantenimiento."})
        if (
            self.genera_recordatorio
            and self.intervalo_meses is None
            and self.intervalo_km is None
        ):
            raise ValidationError(
                {
                    "genera_recordatorio": (
                        "Para activar el recordatorio configurá un intervalo "
                        "en meses, en kilómetros o ambos."
                    )
                }
            )

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
