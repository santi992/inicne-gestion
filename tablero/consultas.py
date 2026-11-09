from datetime import timedelta

from django.utils import timezone

from personal.models import AreaTrabajo
from tareas.models import Tarea

VISTAS = ("hoy", "semana", "todas")


def filtrar_tareas(parametros, persona):
    """
    Devuelve las tareas que corresponde mostrar en el tablero, según los
    filtros del pedido (?vista=...&area=...&mias=1), y los filtros que
    realmente se aplicaron.

    Antes esta lógica estaba dentro de la vista del tablero. La saco a una
    función porque ahora la usan dos: la página con plantillas de Django y
    la API REST que consume React. Así las dos muestran siempre lo mismo.

    "parametros" es un QueryDict (request.GET o request.query_params) y
    "persona" es la Persona del usuario, o None si no tiene ficha.

    Las vistas de tiempo:
    - hoy:    lo atrasado + lo que vence hoy
    - semana: lo atrasado + lo que vence hasta el domingo (la predeterminada)
    - todas:  todo lo abierto, sin límite de fecha
    En las tres, las tareas completadas HOY siguen visibles hasta el final
    del día (regla de Tarea.objects.visibles_en_tablero()).
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
    # "lte" = "less than or equal": fecha límite menor o igual a...
    # Como las atrasadas tienen fecha anterior a hoy, entran solas.
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
    """Los tres números de las tarjetas. Miran a todo el instituto, sin filtros."""
    hoy = timezone.localdate()
    return {
        "vencidas": Tarea.objects.vencidas().count(),
        "por_vencer": Tarea.objects.por_vencer().count(),
        "completadas_hoy": Tarea.objects.filter(
            estado=Tarea.Estado.COMPLETADA, fecha_completada=hoy
        ).count(),
    }
