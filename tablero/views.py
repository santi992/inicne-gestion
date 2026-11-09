from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from personal.models import AreaTrabajo
from personal.permisos import es_administrador, obtener_persona
from tareas.models import COLORES_ALERTA

from .consultas import contadores, filtrar_tareas


def inicio(request):
    """
    Página de entrada del sitio.
    - El visitante (sin sesión) ve la presentación y el botón de ingreso.
    - El usuario con sesión pasa directo al tablero.
    """
    if request.user.is_authenticated:
        return redirect("tablero")
    return render(request, "inicio.html")


class TableroView(LoginRequiredMixin, TemplateView):
    """
    Pantalla principal con plantillas de Django: las tareas del instituto
    con sus alertas. Todo el personal ve TODAS las tareas (decisión del
    proyecto: el director quiere el panorama completo).
    La lógica de filtrado está en consultas.py.
    """

    template_name = "tablero/tablero.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        persona = obtener_persona(self.request.user)
        tareas, filtros = filtrar_tareas(self.request.GET, persona)
        numeros = contadores()

        contexto.update({
            "tareas": tareas,
            "vista": filtros["vista"],
            "solo_mias": filtros["mias"],
            "area_sel": filtros["area"],
            "areas": AreaTrabajo.choices,
            "persona": persona,
            "es_admin": es_administrador(self.request.user),
            "n_vencidas": numeros["vencidas"],
            "n_por_vencer": numeros["por_vencer"],
            "n_completadas_hoy": numeros["completadas_hoy"],
            # Paso los colores del modelo para que las tarjetas usen los mismos
            "colores": {nivel: par[0] for nivel, par in COLORES_ALERTA.items()},
        })
        return contexto


# ensure_csrf_cookie obliga a Django a enviar la cookie "csrftoken" con esta
# página. React la necesita para poder hacer POST: la lee y la manda en un
# encabezado. Las plantillas de Django la reciben solas por {% csrf_token %},
# pero esta página no tiene ningún formulario, así que se la pido a mano.
@method_decorator(ensure_csrf_cookie, name="dispatch")
class TableroEnVivoView(LoginRequiredMixin, TemplateView):
    """
    Página que aloja la aplicación de React (el tablero "en vivo", pensado
    para dejar en una pantalla del instituto: se actualiza solo). Django
    solo entrega la cáscara (barra de navegación y sesión); los datos los
    pide React a la API REST.
    """

    template_name = "tablero/tablero_en_vivo.html"
