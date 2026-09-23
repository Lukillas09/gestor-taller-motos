from django import forms
from django.contrib import admin

from apps.mantenimientos.models import MantenimientoRealizado

from .models import Servicio


class ServicioAdminForm(forms.ModelForm):
    confirmar_kilometraje_menor = forms.BooleanField(
        label="Confirmo el kilometraje menor",
        required=False,
        help_text="Es obligatorio si el valor es menor al último kilometraje de la moto.",
    )

    class Meta:
        model = Servicio
        fields = "__all__"

    def clean(self):
        datos = super().clean()
        moto = datos.get("moto") or getattr(self.instance, "moto", None)
        kilometraje = datos.get("kilometraje")
        kilometraje_cambio = not self.instance.pk or (
            kilometraje != self.instance.kilometraje
        )
        if (
            moto
            and kilometraje is not None
            and moto.kilometraje_actual is not None
            and kilometraje < moto.kilometraje_actual
            and kilometraje_cambio
            and not datos.get("confirmar_kilometraje_menor")
        ):
            self.add_error(
                "confirmar_kilometraje_menor",
                "Confirmá el valor antes de guardar.",
            )
        return datos


class MantenimientoRealizadoInline(admin.TabularInline):
    model = MantenimientoRealizado
    autocomplete_fields = ("tipo_mantenimiento",)
    extra = 0


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    form = ServicioAdminForm
    inlines = (MantenimientoRealizadoInline,)
    list_display = (
        "fecha",
        "moto",
        "cliente",
        "kilometraje",
        "estado",
        "precio_total",
        "creado_por",
    )
    list_filter = ("estado", "fecha")
    search_fields = (
        "moto__patente",
        "moto__marca",
        "moto__modelo",
        "cliente__nombre",
        "cliente__apellido",
        "cliente__telefono",
        "trabajos_adicionales",
    )
    autocomplete_fields = ("moto",)
    readonly_fields = ("cliente", "creado_por", "creado_en", "actualizado_en")
    date_hierarchy = "fecha"
    ordering = ("-fecha", "-pk")
    list_select_related = ("moto", "cliente", "creado_por")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False
