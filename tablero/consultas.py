from datetime import timedelta

from django.utils import timezone

from personal.models import AreaTrabajo
from tareas.models import Tarea

VISTAS = ("hoy", "semana", "todas")


def filtrar_tareas(parametros, persona):
    """
    devuelve las tareas del tablero según los filtros del pedido

    se usa en la página con plantillas de Django y la API REST que consume React

    "parametros" es un QueryDict (request.GET o request.query_params)
    "persona" es la Persona del usuario, o None si no tiene ficha

    vistas de tiempo:
    - hoy:    lo atrasado + lo que vence hoy
    - semana: lo atrasado + lo que vence hasta el domingo
    - todas:  todo lo abierto, sin límite de fecha
    """
    hoy = timezone.localdate()
    # weekday() da 0 para el lunes y 6 para el domingo:
    # sumando lo que falta llego al domingo de esta semana
    domingo = hoy + timedelta(days=6 - hoy.weekday())

    vista = parametros.get("vista", "semana")
    if vista not in VISTAS:
        vista = "semana"

    tareas = Tarea.objects.visibles_en_tablero().select_related(
        "responsable__usuario", "proyecto"
    )
    # "lte" == "less than or equal" fecha límite menor o igual a...
    if vista == "hoy":
        tareas = tareas.filter(fecha_limite__lte=hoy)
    elif vista == "semana":
        tareas = tareas.filter(fecha_limite__lte=domingo)

    solo_mias = parametros.get("mias") in ("1", "true") and persona is not None
    if solo_mias:
        tareas = tareas.filter(responsable=persona)

    area = parametros.get("area", "")
    if area not in AreaTrabajo.values:
        area = ""
    if area:
        tareas = tareas.filter(area=area)

    return tareas, {"vista": vista, "area": area, "mias": solo_mias}


def contadores():
    """
    los tres números de las tarjetas
    miran a todo el instituto, sin filtros
    """

    hoy = timezone.localdate()
    return {
        "vencidas": Tarea.objects.vencidas().count(),
        "por_vencer": Tarea.objects.por_vencer().count(),
        "completadas_hoy": Tarea.objects.filter(
            estado=Tarea.Estado.COMPLETADA, fecha_completada=hoy
        ).count(),
    }
