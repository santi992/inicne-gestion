from personal.permisos import es_administrador, obtener_persona


def puede_cambiar_estado(usuario, tarea):
    """
    Regla de la matriz de roles: el estado de una tarea lo cambia el
    administrador o la persona a quien está asignada. El resto la ve, pero
    no la toca.

    La uso desde dos lugares (la vista normal y la API REST). Si la regla
    estuviera escrita en cada uno, algún día cambiaría uno y el otro no,
    y habría una puerta trasera. Escrita una sola vez, no puede pasar.
    """
    if es_administrador(usuario):
        return True
    persona = obtener_persona(usuario)
    return persona is not None and tarea.responsable_id == persona.pk
