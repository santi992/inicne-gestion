from django.contrib import admin

from .models import Persona


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    # columnas que se ven en el listado del panel de administración
    list_display = ("__str__", "area", "cargo", "rol", "activo")
    # filtros laterales para encontrar gente rápido
    list_filter = ("area", "cargo", "rol", "activo")
    # buscador
    search_fields = ("usuario__first_name", "usuario__last_name", "usuario__username")
