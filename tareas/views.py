from django.shortcuts import redirect, render


def inicio(request):
    """
    página de entrada del sitio.
    visitante sin loguearse ve la presentación y el botón de ingreso
    el usuario logueado pasa al listado de equipos
    """
    if request.user.is_authenticated:
        return redirect("equipamiento:lista")
    return render(request, "inicio.html")
