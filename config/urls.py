from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # uso las vistas de login y logout que ya trae Django
    # LoginView busca la plantilla "registration/login.html", en la carpeta templates/
    # uso estilos de Bootstrap.
    path("ingresar/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    # cada app tiene su propio urls.py y acá solo las enchufo
    path("equipamiento/", include("equipamiento.urls")),
    path("tareas/", include("tareas.urls")),
    path("", include("tablero.urls")),
]
