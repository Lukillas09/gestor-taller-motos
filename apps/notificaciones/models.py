from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class SeguimientoMantenimiento(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        CONTACTADO = "CONTACTADO", "Contactado"
        POSPUESTO = "POSPUESTO", "Pospuesto"
        TURNO_ACORDADO = "TURNO_ACORDADO", "Turno acordado"
        NO_INTERESADO = "NO_INTERESADO", "No interesado"

    mantenimiento_base = models.ForeignKey(
        "mantenimientos.MantenimientoRealizado",
        on_delete=models.PROTECT,
        related_name="seguimientos",
        verbose_name="mantenimiento base",
    )
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="seguimientos_mantenimiento",
        verbose_name="cliente contactado",
    )
    estado = models.CharField(
        "estado",
        max_length=16,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    pospuesto_hasta = models.DateField(
        "pospuesto hasta",
        blank=True,
        null=True,
    )
    turno_para = models.DateTimeField(
        "turno para",
        blank=True,
        null=True,
    )
    ultimo_contacto_en = models.DateTimeField(
        "último contacto el",
        blank=True,
        null=True,
    )
    ultimo_contacto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="último contacto por",
        blank=True,
        null=True,
    )
    observaciones = models.TextField("nota operativa", blank=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="actualizado por",
        blank=True,
        null=True,
    )
    creado_en = models.DateTimeField("creado el", auto_now_add=True)
    actualizado_en = models.DateTimeField("actualizado el", auto_now=True)

    class Meta:
        ordering = ("-actualizado_en", "-pk")
        verbose_name = "seguimiento de mantenimiento"
        verbose_name_plural = "seguimientos de mantenimiento"
        constraints = (
            models.UniqueConstraint(
                fields=("mantenimiento_base", "cliente"),
                name="seguimiento_ciclo_cliente_unico",
            ),
            models.CheckConstraint(
                condition=~Q(estado="POSPUESTO")
                | Q(pospuesto_hasta__isnull=False),
                name="seguimiento_pospuesto_con_fecha",
            ),
            models.CheckConstraint(
                condition=Q(estado="POSPUESTO")
                | Q(pospuesto_hasta__isnull=True),
                name="seguimiento_fecha_solo_pospuesto",
            ),
            models.CheckConstraint(
                condition=~Q(estado="TURNO_ACORDADO")
                | Q(turno_para__isnull=False),
                name="seguimiento_turno_con_fecha",
            ),
            models.CheckConstraint(
                condition=Q(estado="TURNO_ACORDADO")
                | Q(turno_para__isnull=True),
                name="seguimiento_fecha_solo_turno",
            ),
        )

    def clean(self):
        super().clean()
        self.observaciones = (self.observaciones or "").strip()
        errores = {}
        if self.estado == self.Estado.POSPUESTO and self.pospuesto_hasta is None:
            errores["pospuesto_hasta"] = "Un seguimiento pospuesto requiere fecha."
        elif self.estado != self.Estado.POSPUESTO and self.pospuesto_hasta is not None:
            errores["pospuesto_hasta"] = (
                "La fecha de posposición solo corresponde al estado pospuesto."
            )

        if self.estado == self.Estado.TURNO_ACORDADO and self.turno_para is None:
            errores["turno_para"] = "Un turno acordado requiere fecha y hora."
        elif self.estado != self.Estado.TURNO_ACORDADO and self.turno_para is not None:
            errores["turno_para"] = (
                "La fecha del turno solo corresponde al estado turno acordado."
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        realizado = self.mantenimiento_base
        moto = realizado.servicio.moto
        return (
            f"{realizado.tipo_mantenimiento.nombre} — "
            f"{moto.marca} {moto.modelo} — {self.cliente.nombre_completo}"
        )


class EventoSeguimientoMantenimiento(models.Model):
    class Tipo(models.TextChoices):
        CONTACTADO = "CONTACTADO", "Contactado"
        POSPUESTO = "POSPUESTO", "Pospuesto"
        TURNO_ACORDADO = "TURNO_ACORDADO", "Turno acordado"
        NO_INTERESADO = "NO_INTERESADO", "No interesado"
        REABIERTO = "REABIERTO", "Reabierto"
        NOTA = "NOTA", "Nota"

    seguimiento = models.ForeignKey(
        SeguimientoMantenimiento,
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name="seguimiento",
    )
    tipo_evento = models.CharField(
        "tipo de evento",
        max_length=16,
        choices=Tipo.choices,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="usuario",
        blank=True,
        null=True,
    )
    nota = models.TextField("nota", blank=True)
    pospuesto_hasta = models.DateField(
        "pospuesto hasta",
        blank=True,
        null=True,
    )
    turno_para = models.DateTimeField(
        "turno para",
        blank=True,
        null=True,
    )
    creado_en = models.DateTimeField("creado el", auto_now_add=True)

    class Meta:
        ordering = ("creado_en", "pk")
        verbose_name = "evento de seguimiento"
        verbose_name_plural = "eventos de seguimiento"
        constraints = (
            models.CheckConstraint(
                condition=~Q(tipo_evento="POSPUESTO")
                | Q(pospuesto_hasta__isnull=False),
                name="evento_pospuesto_con_fecha",
            ),
            models.CheckConstraint(
                condition=~Q(tipo_evento="TURNO_ACORDADO")
                | Q(turno_para__isnull=False),
                name="evento_turno_con_fecha",
            ),
        )

    def clean(self):
        super().clean()
        self.nota = (self.nota or "").strip()
        errores = {}
        if self.tipo_evento == self.Tipo.POSPUESTO and self.pospuesto_hasta is None:
            errores["pospuesto_hasta"] = "El evento pospuesto requiere fecha."
        if self.tipo_evento == self.Tipo.TURNO_ACORDADO and self.turno_para is None:
            errores["turno_para"] = "El evento de turno requiere fecha y hora."
        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        fecha = self.creado_en.strftime("%d/%m/%Y") if self.creado_en else "sin fecha"
        return f"{self.get_tipo_evento_display()} — {fecha}"
