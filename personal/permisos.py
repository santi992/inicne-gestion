from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


def obtener_persona(usuario):
    """
    devuelve la Persona del usuario
    getattr con un tercer argumento evita errores cuando el usuario
    existe en Django pero no tiene ficha de Persona
    """
    return getattr(usuario, "persona", None)


def es_administrador(usuario):
    """
    True si el usuario tiene rol de administrador o es superusuario
    """
    if not usuario.is_authenticated:
        return False
    if usuario.is_superuser:
        return True
    persona = obtener_persona(usuario)
    return persona is not None and persona.activo and persona.es_administrador


class SoloAdministradorMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    solo da acceso a los administradores:
    si no inició sesión lo manda al login.
    si inició sesión pero no es administrador, devuelve error 403 (prohibido)
    """

    def test_func(self):
        return es_administrador(self.request.user)


class PersonaRequeridaMixin(LoginRequiredMixin):
    """
    para acciones que necesitan saber QUIÉN las hace
    si el usuario no tiene ficha de Personasale un aviso evitando un error.
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
