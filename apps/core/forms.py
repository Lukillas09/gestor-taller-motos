from django import forms


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                clase = "form-check-input"
            elif isinstance(widget, forms.Select):
                clase = "form-select"
            else:
                clase = "form-control"

            clases_actuales = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{clases_actuales} {clase}".strip()
