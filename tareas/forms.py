from django import forms
from django.utils import timezone

from personal.formularios import BootstrapMixin
from personal.models import Persona

from .models import Tarea


class TareaForm(BootstrapMixin, forms.ModelForm):
    """Formulario para crear y editar tareas (solo lo usa el administrador)."""

    class Meta:
        model = Tarea
        fields = [
            "titulo", "descripcion", "proyecto", "area", "responsable",
            "fecha_limite", "prioridad", "estado",
        ]
        widgets = {
            "fecha_limite": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "descripcion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo se puede asignar una tarea a personas activas
        self.fields["responsable"].queryset = (
            Persona.objects.filter(activo=True).select_related("usuario")
        )
        # Una tarea nueva siempre empieza "Pendiente", así que no tiene
        # sentido preguntar el estado al crearla. Al editar sí aparece.
        if not self.instance.pk:
            del self.fields["estado"]

    def clean_fecha_limite(self):
        # clean_<campo> valida un campo en particular.
        # Regla de negocio: no se crean tareas con fecha límite ya pasada.
        # Al EDITAR no la aplico, porque una tarea puede venir atrasada.
        fecha = self.cleaned_data["fecha_limite"]
        if not self.instance.pk and fecha < timezone.localdate():
            raise forms.ValidationError(
                "La fecha límite no puede ser anterior a hoy."
            )
        return fecha
