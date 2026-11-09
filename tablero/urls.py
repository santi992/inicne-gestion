from django.urls import path

from . import api, views

urlpatterns = [
    # name="inicio" me permite escribir {% url 'inicio' %} en las plantillas
    # y redirect("inicio") en las vistas, sin repetir la dirección a mano
    path("", views.inicio, name="inicio"),
    path("tablero/", views.TableroView.as_view(), name="tablero"),
    path("tablero/en-vivo/", views.TableroEnVivoView.as_view(), name="tablero_en_vivo"),
    # API REST que consume la aplicación de React
    path("api/tablero/", api.TableroAPIView.as_view(), name="api_tablero"),
    path("api/tareas/<int:pk>/estado/", api.CambiarEstadoAPIView.as_view(), name="api_tarea_estado"),
]
