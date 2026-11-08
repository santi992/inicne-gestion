from django.shortcuts import redirect, render


def inicio(request):
    """
    Página de entrada del sitio.
    - El visitante (sin sesión) ve la presentación y el botón de ingreso.
    - El usuario con sesión pasa directo a la aplicación.
    Por ahora lo mando al listado de equipos. Cuando exista el tablero
    (día 4), cambio este redirect para que vaya allí.
    """
    if request.user.is_authenticated:
        return redirect("equipamiento:lista")
    return render(request, "inicio.html")
