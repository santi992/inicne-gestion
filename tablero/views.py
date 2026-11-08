from django.shortcuts import redirect, render


def inicio(request):
    """
    Página de entrada del sitio.
    el usuario no logueado ve la presentación y el botón de ingreso.
    el usuario logueado pasa al listado de equipos
    """
    if request.user.is_authenticated:
        return redirect("equipamiento:lista")
    return render(request, "inicio.html")
