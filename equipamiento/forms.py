from django import forms

from personal.formularios import BootstrapMixin
from personal.models import Persona

from .models import Equipo, Movimiento


def equipos_disponibles():
    """
    Equipos que se pueden retirar ahora: los que no están fuera de servicio
    ni dados de baja, y que no tienen un retiro sin devolver.
    """
    # Subconsulta: los equipos con algún movimiento sin fecha de devolución
    retirados = Movimiento.objects.filter(fecha_devolucion__isnull=True).values(
        "equipo_id"
    )
    return Equipo.objects.exclude(
        estado__in=[Equipo.Estado.FUERA_DE_SERVICIO, Equipo.Estado.BAJA]
    ).exclude(pk__in=retirados)


class EquipoForm(BootstrapMixin, forms.ModelForm):
    """Formulario para crear y editar equipos (solo lo usa el administrador)."""

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
        # solo personas activas pueden ser responsables
        self.fields["responsable"].queryset = Persona.objects.filter(
            activo=True
        ).select_related("usuario")


class RetiroForm(BootstrapMixin, forms.ModelForm):
    """
    formulario para retirar un equipo
    Persona y fechas se autocompletan
    """

    class Meta:
        model = Movimiento
        fields = ["equipo", "actividad", "observaciones"]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # si alguien manipula el formulario y manda otro equipo, Django lo
        # rechaza porque no figura entre las opciones válidas
        self.fields["equipo"].queryset = equipos_disponibles()


class DevolucionForm(BootstrapMixin, forms.ModelForm):
    """
    formulario para devolver un equipo: pide el estado en que vuelve
    """

    class Meta:
        model = Movimiento
        fields = ["estado_devolucion", "observaciones"]
        widgets = {"observaciones": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # blank=True al retirar en el formulario
        # se completa al devolver
        self.fields["estado_devolucion"].required = True
