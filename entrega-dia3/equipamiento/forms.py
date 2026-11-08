from django import forms

from personal.models import Persona

from .models import Equipo, Movimiento


class BootstrapMixin:
    """
    Agrega a cada campo del formulario la clase CSS que Bootstrap necesita.
    Lo hago acá una sola vez en lugar de repetir attrs={"class": ...} en
    cada campo de cada formulario.
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


def equipos_disponibles():
    """
    Equipos que se pueden retirar ahora: los que no están fuera de servicio
    ni dados de baja, y que no tienen un retiro sin devolver.
    """
    # Subconsulta: los equipos con algún movimiento sin fecha de devolución
    retirados = Movimiento.objects.filter(
        fecha_devolucion__isnull=True
    ).values("equipo_id")
    return (
        Equipo.objects
        .exclude(estado__in=[Equipo.Estado.FUERA_DE_SERVICIO, Equipo.Estado.BAJA])
        .exclude(pk__in=retirados)
    )


class EquipoForm(BootstrapMixin, forms.ModelForm):
    """Formulario para crear y editar equipos (solo lo usa el administrador)."""

    class Meta:
        model = Equipo
        fields = [
            "codigo", "nombre", "categoria", "ubicacion", "estado",
            "fecha_ultima_revision", "responsable", "observaciones",
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
        # Solo ofrezco como responsables a personas activas
        self.fields["responsable"].queryset = (
            Persona.objects.filter(activo=True).select_related("usuario")
        )


class RetiroForm(BootstrapMixin, forms.ModelForm):
    """
    Formulario para retirar un equipo. No pide quién retira ni la fecha:
    esos datos los completa la vista (usuario logueado y hora actual), así
    nadie puede registrar un retiro a nombre de otra persona.
    """

    class Meta:
        model = Movimiento
        fields = ["equipo", "actividad", "observaciones"]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limito las opciones del desplegable. También sirve de seguridad:
        # si alguien manipula el formulario y manda otro equipo, Django lo
        # rechaza porque no figura entre las opciones válidas.
        self.fields["equipo"].queryset = equipos_disponibles()


class DevolucionForm(BootstrapMixin, forms.ModelForm):
    """Formulario para devolver un equipo: pide el estado en que vuelve."""

    class Meta:
        model = Movimiento
        fields = ["estado_devolucion", "observaciones"]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # En el modelo el campo es opcional (blank=True) porque un retiro
        # recién hecho todavía no tiene estado de devolución. Pero al
        # devolver, es obligatorio.
        self.fields["estado_devolucion"].required = True
