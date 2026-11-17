from django import forms


class BootstrapMixin:
    """
    agrega a cada campo del formulario la clase CSS que Bootstrap necesita
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            widget = campo.widget
            if isinstance(widget, forms.CheckboxInput):
                clase = "form-check-input"
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                clase = "form-select"
            else:
                clase = "form-control"
            widget.attrs["class"] = (
                widget.attrs.get("class", "") + " " + clase
            ).strip()
