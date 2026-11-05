from django.contrib import admin

from .models import Actividad, Categoria, Equipo, Movimiento, Ubicacion

# catálogos simples
admin.site.register(Categoria)
admin.site.register(Ubicacion)
admin.site.register(Actividad)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "nombre",
        "categoria",
        "ubicacion",
        "estado",
        "fecha_ultima_revision",
        "responsable",
    )
    list_filter = ("estado", "categoria", "ubicacion")
    search_fields = ("codigo", "nombre")


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "equipo",
        "persona_retira",
        "actividad",
        "fecha_retiro",
        "fecha_devolucion",
        "estado_devolucion",
    )
    list_filter = ("actividad", "estado_devolucion")
    search_fields = ("equipo__codigo", "equipo__nombre")
