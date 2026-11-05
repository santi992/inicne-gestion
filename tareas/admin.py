from django.contrib import admin

from django.utils.html import format_html

from .models import Proyecto, Tarea


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "director", "fecha_inicio", "fecha_fin")
    # filter_horizontal da un selector doble para el muchos a muchos
    filter_horizontal = ("colaboradores",)
    search_fields = ("nombre",)


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "area",
        "responsable",
        "fecha_limite",
        "estado",
        "prioridad",
        "nivel_alerta",
    )
    list_filter = ("estado", "prioridad", "area")
    search_fields = ("titulo", "responsable__usuario__last_name")

    # columna personalizada con una "etiqueta" con el color de la alerta
    # ordering le dice al admin por qué campo real ordenar al hacer clic
    @admin.display(description="Alerta", ordering="fecha_limite")
    def alerta(self, obj):
        fondo, texto = obj.colores_alerta
        # format_html arma el HTML de forma segura
        # escapa los valores para que nadie pueda colar código malicioso
        # si usara un f-string común, el admin no mostraría el HTML
        return format_html(
            '<span style="background:{}; color:{}; padding:3px 10px; '
            'border-radius:12px; font-weight:bold;">{}</span>',
            fondo,
            texto,
            obj.etiqueta_alerta,
        )
