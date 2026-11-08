from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Uso las vistas de login y logout que ya trae Django, no escribo las mías.
    # LoginView busca la plantilla "registration/login.html", que creo yo
    # en la carpeta templates/ con estilos de Bootstrap.
    path("ingresar/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    # Cada app tiene su propio urls.py y acá solo las enchufo
    path("equipamiento/", include("equipamiento.urls")),
    path("", include("tablero.urls")),
]
