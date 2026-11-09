from django.urls import path

from . import views

app_name = "tareas"

urlpatterns = [
    path("nueva/", views.TareaCreateView.as_view(), name="crear"),
    path("<int:pk>/editar/", views.TareaUpdateView.as_view(), name="editar"),
    path("<int:pk>/eliminar/", views.TareaDeleteView.as_view(), name="eliminar"),
    path("<int:pk>/estado/", views.CambiarEstadoView.as_view(), name="estado"),
]
