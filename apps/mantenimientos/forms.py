from django import forms

from apps.core.forms import BootstrapFormMixin

from .models import TipoMantenimiento


class TipoMantenimientoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TipoMantenimiento
        fields = (
            "nombre",
            "descripcion",
            "activo",
            "genera_recordatorio",
            "intervalo_meses",
            "intervalo_km",
            "aviso_dias",
            "aviso_km",
        )
        labels = {
            "genera_recordatorio": "Participa en alertas de mantenimiento",
            "intervalo_meses": "Cada cuántos meses",
            "intervalo_km": "Cada cuántos kilómetros",
            "aviso_dias": "Avisar cuántos días antes",
            "aviso_km": "Avisar cuántos kilómetros antes",
        }
        help_texts = {
            "activo": "Los tipos inactivos se conservan en el historial.",
            "genera_recordatorio": (
                "Debe existir al menos un intervalo para activar las alertas."
            ),
            "intervalo_meses": "Opcional. Se calcula por meses calendario.",
            "intervalo_km": (
                "Opcional. Usa únicamente el último kilometraje conocido."
            ),
        }
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "intervalo_meses": forms.NumberInput(attrs={"min": 1}),
            "intervalo_km": forms.NumberInput(
                attrs={"min": 1, "inputmode": "numeric"}
            ),
            "aviso_dias": forms.NumberInput(attrs={"min": 0}),
            "aviso_km": forms.NumberInput(
                attrs={"min": 0, "inputmode": "numeric"}
            ),
        }
