from django.urls import path

from . import views

urlpatterns = [
    # name="inicio" para escribir {% url 'inicio' %} en las plantillas
    path("", views.inicio, name="inicio"),
]
