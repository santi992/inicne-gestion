from django.urls import path

from . import views

# app_name crea un "espacio de nombres": así escribo {% url 'equipamiento:lista' %}
# y no se confunde con una vista llamada "lista" de otra app.
app_name = "equipamiento"

urlpatterns = [
    path("", views.EquipoListView.as_view(), name="lista"),
    path("nuevo/", views.EquipoCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", views.EquipoUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.EquipoDeleteView.as_view(), name="eliminar"),
    path("movimientos/", views.MovimientoListView.as_view(), name="movimientos"),
    path("movimientos/retirar/", views.RetirarView.as_view(), name="retirar"),
    path("movimientos/<int:pk>/devolver/", views.DevolverView.as_view(), name="devolver"),
]
