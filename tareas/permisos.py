from personal.permisos import es_administrador, obtener_persona


def puede_cambiar_estado(usuario, tarea):
    """
    el estado de una tarea solo puede ser cambiado por el
    administrador o la persona a quien está asignada
    """
    if es_administrador(usuario):
        return True
    persona = obtener_persona(usuario)
    return persona is not None and tarea.responsable_id == persona.pk
