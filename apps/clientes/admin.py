from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "telefono", "email", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "apellido", "telefono", "email")
    ordering = ("apellido", "nombre")
    readonly_fields = ("creado_en", "actualizado_en")

    def has_delete_permission(self, request, obj=None):
        return False
