from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from personal.permisos import (
    PersonaRequeridaMixin,
    SoloAdministradorMixin,
    es_administrador,
    obtener_persona,
)

from .forms import DevolucionForm, EquipoForm, RetiroForm
from .models import Categoria, Equipo, Movimiento

# ---------------------------------------------------------------------------
# Equipos
# ---------------------------------------------------------------------------


class EquipoListView(LoginRequiredMixin, ListView):
    """
    listado de equipos con buscador y filtros
    lo ve cualquier usuario logueado
    """

    model = Equipo
    template_name = "equipamiento/equipo_list.html"
    paginate_by = 20  # 20 equipos por página

    def get_queryset(self):
        # select_related trae las tablas relacionadas en la misma consulta SQL
        consulta = Equipo.objects.select_related(
            "categoria", "ubicacion", "responsable__usuario"
        )
        texto = self.request.GET.get("q", "").strip()
        estado = self.request.GET.get("estado", "")
        categoria = self.request.GET.get("categoria", "")

        if texto:
            # icontains == contiene el texto sin distinguir mayúsculas
            consulta = consulta.filter(
                Q(codigo__icontains=texto) | Q(nombre__icontains=texto)
            )
        if estado in Equipo.Estado.values:
            consulta = consulta.filter(estado=estado)
        # isdigit() evita un error si alguien escribe basura en la dirección
        if categoria.isdigit():
            consulta = consulta.filter(categoria_id=int(categoria))
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["categorias"] = Categoria.objects.all()
        contexto["estados"] = Equipo.Estado.choices
        contexto["q"] = self.request.GET.get("q", "")
        contexto["estado_sel"] = self.request.GET.get("estado", "")
        contexto["categoria_sel"] = self.request.GET.get("categoria", "")
        # al cambiar de página se conservsn los filtros
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["filtros"] = parametros.urlencode()
        # muestra u oculta los botones de editar
        contexto["es_admin"] = es_administrador(self.request.user)
        return contexto


class EquipoCreateView(SoloAdministradorMixin, SuccessMessageMixin, CreateView):
    model = Equipo
    form_class = EquipoForm
    template_name = "equipamiento/equipo_form.html"
    success_url = reverse_lazy("equipamiento:lista")
    success_message = "Equipo creado correctamente."
    extra_context = {"titulo": "Nuevo equipo"}


class EquipoUpdateView(SoloAdministradorMixin, SuccessMessageMixin, UpdateView):
    model = Equipo
    form_class = EquipoForm
    template_name = "equipamiento/equipo_form.html"
    success_url = reverse_lazy("equipamiento:lista")
    success_message = "Equipo actualizado correctamente."
    extra_context = {"titulo": "Editar equipo"}


class EquipoDeleteView(SoloAdministradorMixin, DeleteView):
    model = Equipo
    template_name = "equipamiento/equipo_confirm_delete.html"
    success_url = reverse_lazy("equipamiento:lista")

    def form_valid(self, form):
        try:
            respuesta = super().form_valid(form)
        except ProtectedError:
            # muestra un mensaje de "baja" en lugar de "eliminar" al intentar borrar un equipo
            messages.error(
                self.request,
                "No se puede eliminar: el equipo tiene movimientos registrados. "
                "Cambiá su estado a 'Baja' para conservar el historial.",
            )
            return redirect("equipamiento:lista")
        messages.success(self.request, "Equipo eliminado.")
        return respuesta


# ---------------------------------------------------------------------------
# Movimientos (retiros y devoluciones)
# ---------------------------------------------------------------------------


class MovimientoListView(LoginRequiredMixin, ListView):
    model = Movimiento
    template_name = "equipamiento/movimiento_list.html"
    paginate_by = 25

    def get_queryset(self):
        consulta = Movimiento.objects.select_related(
            "equipo",
            "actividad",
            "persona_retira__usuario",
            "persona_devuelve__usuario",
        )
        # ?pendientes=1 muestra solo los equipos que siguen afuera
        if self.request.GET.get("pendientes") == "1":
            consulta = consulta.filter(fecha_devolucion__isnull=True)
        return consulta

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["solo_pendientes"] = self.request.GET.get("pendientes") == "1"
        return contexto


class RetirarView(PersonaRequeridaMixin, SuccessMessageMixin, CreateView):
    model = Movimiento
    form_class = RetiroForm
    template_name = "equipamiento/movimiento_form.html"
    success_url = reverse_lazy("equipamiento:movimientos")
    success_message = "Retiro registrado."
    extra_context = {"titulo": "Retirar equipo"}

    def get_initial(self):
        # si el usuario llega desde el botón "Retirar" de un equipo
        # el desplegable muestra ese equipo ya elegido
        # (?equipo=ID en la dirección)
        inicial = super().get_initial()
        equipo = self.request.GET.get("equipo", "")
        if equipo.isdigit():
            inicial["equipo"] = int(equipo)
        return inicial

    def form_valid(self, form):
        # selecciona el usuario logueado automáticamente
        form.instance.persona_retira = obtener_persona(self.request.user)
        return super().form_valid(form)


class DevolverView(PersonaRequeridaMixin, SuccessMessageMixin, UpdateView):
    model = Movimiento
    form_class = DevolucionForm
    template_name = "equipamiento/devolucion_form.html"
    success_url = reverse_lazy("equipamiento:movimientos")
    success_message = "Devolución registrada."

    def get_queryset(self):
        # solo se pueden devolver los movimientos pendientes
        # si alguien intenta devolver un equipo ya devuelto devuelve 404
        return Movimiento.objects.filter(fecha_devolucion__isnull=True).select_related(
            "equipo", "persona_retira__usuario"
        )

    def form_valid(self, form):
        movimiento = form.save(commit=False)
        movimiento.persona_devuelve = obtener_persona(self.request.user)
        movimiento.fecha_devolucion = timezone.now()
        # atomic() guarda movimiento y estado del equipo si o si o no guarda nada
        with transaction.atomic():
            movimiento.save()
            equipo = movimiento.equipo
            # el equipo se guarda con estado según informó quien lo devuelve
            equipo.estado = movimiento.estado_devolucion
            equipo.save(update_fields=["estado"])
        messages.success(self.request, self.success_message)
        return redirect(self.success_url)
