from django.contrib import admin

from .models import TipoMantenimiento


@admin.register(TipoMantenimiento)
class TipoMantenimientoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "actualizado_en")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")
    ordering = ("nombre",)
    readonly_fields = ("creado_en", "actualizado_en")

    def has_delete_permission(self, request, obj=None):
        return False
