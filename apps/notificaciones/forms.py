from datetime import timedelta

from django import forms
from django.utils import timezone

from apps.core.forms import BootstrapFormMixin
from apps.mantenimientos.services import EstadoMantenimiento


class AlertasSeguimientoFiltroForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.SearchInput(
            attrs={
                "placeholder": "Patente, moto, cliente o teléfono",
                "autocomplete": "off",
            }
        ),
    )
    estado = forms.ChoiceField(
        label="Estado técnico",
        required=False,
        choices=(
            ("", "Todos"),
            (EstadoMantenimiento.VENCIDO.value, "Vencidos"),
            (EstadoMantenimiento.PROXIMO.value, "Próximos"),
        ),
    )
    tipo = forms.ChoiceField(
        label="Mantenimiento",
        required=False,
        choices=(("", "Todos"),),
    )
    seguimiento = forms.ChoiceField(
        label="Seguimiento",
        choices=(
            ("accionables", "Requieren atención"),
            ("todos", "Todos"),
            ("contactados", "Contactados"),
            ("pospuestos", "Pospuestos"),
            ("turnos", "Con turno"),
            ("no_interesados", "No interesados"),
        ),
        initial="accionables",
    )

    def __init__(self, *args, tipos_mantenimiento=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].choices = (
            ("", "Todos"),
            *((str(tipo.pk), tipo.nombre) for tipo in tipos_mantenimiento),
        )


class SeguimientoBaseForm(BootstrapFormMixin, forms.Form):
    mantenimiento_base = forms.IntegerField(
        min_value=1,
        widget=forms.HiddenInput,
    )


class ContactoForm(SeguimientoBaseForm):
    nota = forms.CharField(
        label="Nota opcional",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class PosponerForm(SeguimientoBaseForm):
    class Plazo:
        SIETE_DIAS = "7"
        QUINCE_DIAS = "15"
        TREINTA_DIAS = "30"
        PERSONALIZADA = "personalizada"

    plazo = forms.ChoiceField(
        label="Recordar",
        choices=(
            (Plazo.SIETE_DIAS, "En 7 días"),
            (Plazo.QUINCE_DIAS, "En 15 días"),
            (Plazo.TREINTA_DIAS, "En 30 días"),
            (Plazo.PERSONALIZADA, "Fecha personalizada"),
        ),
    )
    fecha_personalizada = forms.DateField(
        label="Fecha personalizada",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    nota = forms.CharField(
        label="Nota opcional",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, hoy=None, **kwargs):
        self.hoy = hoy or timezone.localdate()
        super().__init__(*args, **kwargs)

    def clean(self):
        datos = super().clean()
        plazo = datos.get("plazo")
        if plazo == self.Plazo.PERSONALIZADA:
            fecha = datos.get("fecha_personalizada")
            if fecha is None:
                self.add_error(
                    "fecha_personalizada",
                    "Elegí la fecha hasta la que querés posponer.",
                )
                return datos
        elif plazo in {
            self.Plazo.SIETE_DIAS,
            self.Plazo.QUINCE_DIAS,
            self.Plazo.TREINTA_DIAS,
        }:
            fecha = self.hoy + timedelta(days=int(plazo))
        else:
            return datos

        if fecha <= self.hoy:
            self.add_error(
                "fecha_personalizada",
                "La fecha para recordar debe ser posterior a hoy.",
            )
        else:
            datos["pospuesto_hasta"] = fecha
        return datos


class TurnoForm(SeguimientoBaseForm):
    turno_para = forms.DateTimeField(
        label="Fecha y hora del turno",
        input_formats=("%Y-%m-%dT%H:%M",),
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )
    nota = forms.CharField(
        label="Nota opcional",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, ahora=None, **kwargs):
        self.ahora = ahora or timezone.now()
        super().__init__(*args, **kwargs)

    def clean_turno_para(self):
        turno_para = self.cleaned_data["turno_para"]
        if timezone.is_naive(turno_para):
            turno_para = timezone.make_aware(
                turno_para,
                timezone.get_current_timezone(),
            )
        if turno_para <= self.ahora:
            raise forms.ValidationError("El turno debe ser posterior al momento actual.")
        return turno_para


class NoInteresadoForm(SeguimientoBaseForm):
    nota = forms.CharField(
        label="Motivo opcional",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class ReabrirForm(SeguimientoBaseForm):
    nota = forms.CharField(
        label="Nota opcional",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class NotaForm(SeguimientoBaseForm):
    nota = forms.CharField(
        label="Nota",
        widget=forms.Textarea(attrs={"rows": 2}),
    )
