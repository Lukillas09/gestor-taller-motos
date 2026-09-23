from django.contrib import admin

from .models import Moto


@admin.register(Moto)
class MotoAdmin(admin.ModelAdmin):
    list_display = (
        "patente",
        "marca",
        "modelo",
        "cliente",
        "kilometraje_actual",
        "activo",
    )
    list_filter = ("activo", "marca")
    search_fields = (
        "patente",
        "marca",
        "modelo",
        "cliente__nombre",
        "cliente__apellido",
        "cliente__telefono",
    )
    list_select_related = ("cliente",)
    autocomplete_fields = ("cliente",)
    ordering = ("marca", "modelo")
    readonly_fields = ("creado_en", "actualizado_en")

    def has_delete_permission(self, request, obj=None):
        return False
