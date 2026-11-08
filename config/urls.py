from django.contrib import admin

from django.contrib.auth import views as auth_views

from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # vistas de login y logout por defecto de Django
    # LoginView busca la plantilla "registration/login.html en la carpeta templates
    path("ingresar/", auth_views.LoginView.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("equipamiento/", include("equipamiento.urls")),
    path("", include("tablero.urls")),
]
