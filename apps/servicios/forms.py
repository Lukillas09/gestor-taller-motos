from django import forms
from django.db.models import Q
from django.urls import reverse

from apps.core.forms import BootstrapFormMixin
from apps.mantenimientos.models import TipoMantenimiento
from apps.motos.models import Moto

from .models import Servicio


class MotoServicioChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, moto):
        patente = moto.patente or "Sin patente"
        return (
            f"{patente} — {moto.marca} {moto.modelo} — "
            f"{moto.cliente.nombre_completo}"
        )


class ServicioForm(BootstrapFormMixin, forms.ModelForm):
    moto = MotoServicioChoiceField(
        label="Moto",
        queryset=Moto.objects.none(),
        empty_label="Seleccioná una moto",
    )
    mantenimientos = forms.ModelMultipleChoiceField(
        label="Trabajos de mantenimiento",
        queryset=TipoMantenimiento.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Marcá todos los trabajos realizados en esta visita.",
    )
    confirmar_kilometraje_menor = forms.BooleanField(
        label="Confirmo que el kilometraje ingresado es menor al último registrado",
        required=False,
        help_text=(
            "Usá esta confirmación sólo si verificaste que el valor histórico es correcto. "
            "La ficha de la moto no reducirá su último kilometraje conocido."
        ),
    )

    class Meta:
        model = Servicio
        fields = (
            "moto",
            "fecha",
            "kilometraje",
            "estado",
            "trabajos_adicionales",
            "observaciones",
            "precio_total",
        )
        labels = {
            "moto": "Moto",
            "trabajos_adicionales": "Otros trabajos realizados",
            "precio_total": "Precio total",
        }
        help_texts = {
            "kilometraje": "Kilometraje registrado al recibir o entregar la moto.",
            "trabajos_adicionales": (
                "Detallá reparaciones o tareas que no aparecen en la lista."
            ),
        }
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "kilometraje": forms.NumberInput(
                attrs={"inputmode": "numeric", "min": 0}
            ),
            "trabajos_adicionales": forms.Textarea(attrs={"rows": 4}),
            "observaciones": forms.Textarea(attrs={"rows": 4}),
            "precio_total": forms.NumberInput(
                attrs={"inputmode": "decimal", "min": 0, "step": "0.01"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            self.fields.pop("moto")
            tipos_actuales = self.instance.mantenimientos_realizados.values_list(
                "tipo_mantenimiento_id", flat=True
            )
            self.fields["mantenimientos"].queryset = TipoMantenimiento.objects.filter(
                Q(activo=True) | Q(pk__in=tipos_actuales)
            ).order_by("nombre", "pk")
            self.initial.setdefault("mantenimientos", list(tipos_actuales))
        else:
            motos = Moto.objects.filter(
                activo=True,
                cliente__activo=True,
            ).select_related("cliente")
            self.fields["moto"].queryset = motos.order_by(
                "patente", "marca", "modelo", "pk"
            )
            self.fields["moto"].widget.attrs.update(
                {
                    "hx-get": reverse("servicios:moto_context"),
                    "hx-trigger": "change",
                    "hx-target": "#moto-contexto",
                    "hx-swap": "innerHTML",
                }
            )
            self.fields["mantenimientos"].queryset = (
                TipoMantenimiento.objects.filter(activo=True).order_by("nombre", "pk")
            )

        self.fields["mantenimientos"].widget.attrs.pop("class", None)

    def clean(self):
        datos = super().clean()
        moto = self.instance.moto if self.instance.pk else datos.get("moto")
        kilometraje = datos.get("kilometraje")
        confirmado = datos.get("confirmar_kilometraje_menor")

        kilometraje_cambio = not self.instance.pk or (
            kilometraje != self.instance.kilometraje
        )
        if (
            moto
            and kilometraje is not None
            and moto.kilometraje_actual is not None
            and kilometraje < moto.kilometraje_actual
            and kilometraje_cambio
            and not confirmado
        ):
            self.add_error(
                "confirmar_kilometraje_menor",
                (
                    "Confirmá el kilometraje menor para guardar este servicio. "
                    f"El último registrado es {moto.kilometraje_actual:,} km."
                ).replace(",", "."),
            )
        return datos


class ServicioFiltroForm(BootstrapFormMixin, forms.Form):
    q = forms.CharField(
        label="Buscar",
        required=False,
        widget=forms.SearchInput(
            attrs={
                "placeholder": "Patente, moto, cliente, teléfono o trabajo",
                "autocomplete": "off",
            }
        ),
    )
    estado = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=(("", "Todos"), *Servicio.Estado.choices),
    )
    desde = forms.DateField(
        label="Desde",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    hasta = forms.DateField(
        label="Hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def clean(self):
        datos = super().clean()
        desde = datos.get("desde")
        hasta = datos.get("hasta")
        if desde and hasta and desde > hasta:
            raise forms.ValidationError(
                "La fecha desde no puede ser posterior a la fecha hasta."
            )
        return datos
