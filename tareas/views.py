from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from personal.permisos import SoloAdministradorMixin

from .forms import TareaForm
from .models import Tarea
from .permisos import puede_cambiar_estado

# No hay una vista "lista de tareas" acá: el listado ES el tablero (app tablero).
# Esta app solo tiene las acciones sobre una tarea.


class TareaCreateView(SoloAdministradorMixin, SuccessMessageMixin, CreateView):
    """Crear tareas: solo el administrador (decisión del proyecto)."""

    model = Tarea
    form_class = TareaForm
    template_name = "tareas/tarea_form.html"
    success_url = reverse_lazy("tablero")
    success_message = "Tarea creada correctamente."
    extra_context = {"titulo": "Nueva tarea"}


class TareaUpdateView(SoloAdministradorMixin, SuccessMessageMixin, UpdateView):
    model = Tarea
    form_class = TareaForm
    template_name = "tareas/tarea_form.html"
    success_url = reverse_lazy("tablero")
    success_message = "Tarea actualizada correctamente."
    extra_context = {"titulo": "Editar tarea"}


class TareaDeleteView(SoloAdministradorMixin, SuccessMessageMixin, DeleteView):
    model = Tarea
    template_name = "tareas/tarea_confirm_delete.html"
    success_url = reverse_lazy("tablero")
    success_message = "Tarea eliminada."


class CambiarEstadoView(LoginRequiredMixin, View):
    """
    Cambia el estado de una tarea (Iniciar, Completar, Reabrir).
    Lo puede hacer el administrador o la persona a quien está asignada la
    tarea; el resto del personal solo la ve. Solo acepta POST porque
    modifica datos: con un enlace común (GET) cualquier página externa
    podría disparar el cambio sin que el usuario se entere.
    """

    http_method_names = ["post"]

    def post(self, request, pk):
        tarea = get_object_or_404(Tarea, pk=pk)
        # La regla de quién puede cambiar el estado vive en tareas/permisos.py,
        # porque la API REST (día 5) necesita exactamente la misma regla
        if not puede_cambiar_estado(request.user, tarea):
            # PermissionDenied muestra la página 403
            raise PermissionDenied

        nuevo_estado = request.POST.get("estado", "")
        # Nunca confío en lo que manda el navegador: valido que sea un estado real
        if nuevo_estado not in Tarea.Estado.values:
            messages.error(request, "Estado no válido.")
        else:
            tarea.estado = nuevo_estado
            # save() del modelo completa o borra fecha_completada solo
            tarea.save()
            messages.success(
                request, f"«{tarea.titulo}»: {tarea.get_estado_display().lower()}."
            )

        # "next" dice a qué página volver (la del tablero con sus filtros).
        # Compruebo que sea una dirección de MI sitio: si no, alguien podría
        # armar un formulario que redirija a una página maliciosa.
        destino = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            destino = reverse("tablero")
        return redirect(destino)
