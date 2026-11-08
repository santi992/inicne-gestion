from django.urls import path

from . import views

urlpatterns = [
    # name="inicio" me permite escribir {% url 'inicio' %} en las plantillas
    # y redirect("inicio") en las vistas, sin repetir la dirección a mano
    path("", views.inicio, name="inicio"),
]
