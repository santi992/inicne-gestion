from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


def obtener_persona(usuario):
    """
    Devuelve la Persona del usuario, o None si todavía no tiene una.
    getattr con un tercer argumento evita que explote cuando el usuario
    existe en Django pero nadie le creó su ficha de Persona.
    """
    return getattr(usuario, "persona", None)


def es_administrador(usuario):
    """True si el usuario tiene rol de administrador (o es superusuario)."""
    if not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    persona = obtener_persona(usuario)
    return persona is not None and persona.activo and persona.es_administrador


class SoloAdministradorMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Un "mixin" es una clase pequeña que le agrega una capacidad a una vista.
    Este deja entrar solo a los administradores:
    - Si no inició sesión, lo manda al login.
    - Si inició sesión pero no es administrador, devuelve error 403
      (prohibido). Para el Personal registrado, esa es la regla de la matriz
      de roles de mi memoria.
    """

    def test_func(self):
        return es_administrador(self.request.user)


class PersonaRequeridaMixin(LoginRequiredMixin):
    """
    Para las acciones que necesitan saber QUIÉN las hace (retirar un equipo).
    Si el usuario no tiene ficha de Persona, no puedo registrar su nombre,
    así que le aviso en lugar de dejar que la vista falle con un error.
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and obtener_persona(request.user) is None:
            messages.error(
                request,
                "Tu usuario no tiene una ficha de Persona. "
                "Pedile al administrador que la cree.",
            )
            return redirect("equipamiento:lista")
        return super().dispatch(request, *args, **kwargs)
