from django import forms

from personal.models import Persona

from .models import Equipo, Movimiento


class BootstrapMixin:
    """
    agrega a cada campo del formulario la correspondiente clase CSS para Bootstrap
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


def equipos_disponibles():
    """
    devuelve los equipos disponibles que se pueden retirar
    """
    # subconsulta de los equipos sin fecha de devolución
    retirados = Movimiento.objects.filter(fecha_devolucion__isnull=True).values(
        "equipo_id"
    )
    return Equipo.objects.exclude(
        estado__in=[Equipo.Estado.FUERA_DE_SERVICIO, Equipo.Estado.BAJA]
    ).exclude(pk__in=retirados)


class EquipoForm(BootstrapMixin, forms.ModelForm):
    """
    formulario para crear y editar equipos
    """

    class Meta:
        model = Equipo
        fields = [
            "codigo",
            "nombre",
            "categoria",
            "ubicacion",
            "estado",
            "fecha_ultima_revision",
            "responsable",
            "observaciones",
        ]
        widgets = {
            # type="date" hace que el navegador muestre un calendario
            "fecha_ultima_revision": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "observaciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["responsable"].queryset = Persona.objects.filter(
            activo=True
        ).select_related("usuario")


class RetiroForm(BootstrapMixin, forms.ModelForm):
    """
    formulario para retirar un equipo
    usuario y fecha se autocompletan (usuario logueado y hora actual)
    """

    class Meta:
        model = Movimiento
        fields = ["equipo", "actividad", "observaciones"]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # limita las opciones del desplegable
        # si alguien manipula el formulario y manda otro equipo, se rechaza
        self.fields["equipo"].queryset = equipos_disponibles()


class DevolucionForm(BootstrapMixin, forms.ModelForm):
    """
    formulario para devolver un equipo
    """

    class Meta:
        model = Movimiento
        fields = ["estado_devolucion", "observaciones"]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # blank=True para retiros
        # .required para devoluciones
        self.fields["estado_devolucion"].required = True
