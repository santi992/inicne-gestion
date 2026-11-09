from django import forms


class BootstrapMixin:
    """
    Agrega a cada campo del formulario la clase CSS que Bootstrap necesita.
    Lo hago acá una sola vez en lugar de repetir attrs={"class": ...} en
    cada campo de cada formulario.

    Antes vivía dentro de equipamiento/forms.py. Lo muevo a la app "personal"
    porque ahora lo usan equipamiento Y tareas, y no quiero que una app
    dependa de los archivos internos de otra. (personal es la app base:
    las demás ya dependen de ella.)
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
            widget.attrs["class"] = (widget.attrs.get("class", "") + " " + clase).strip()
