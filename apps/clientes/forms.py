from django import forms

from apps.core.forms import BootstrapFormMixin

from .models import Cliente


class ClienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Cliente
        fields = (
            "nombre",
            "apellido",
            "telefono",
            "email",
            "direccion",
            "observaciones",
        )
        widgets = {
            "nombre": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "apellido": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "telefono": forms.TextInput(
                attrs={"autocomplete": "tel", "inputmode": "tel"}
            ),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "direccion": forms.TextInput(attrs={"autocomplete": "street-address"}),
            "observaciones": forms.Textarea(attrs={"rows": 4}),
        }
        error_messages = {
            "nombre": {"required": "Ingresá el nombre del cliente."},
        }
