from django.contrib import admin

from .models import ControlDiario, Estanque, Lote

admin.site.register(Estanque)
admin.site.register(Lote)


@admin.register(ControlDiario)
class ControlDiarioAdmin(admin.ModelAdmin):
    list_display = (
        "estanque",
        "fecha",
        "turno",
        "responsable",
        "soporte_vital_ok",
        "estado_general",
        "mortalidad",
    )
    list_filter = ("estanque", "turno", "estado_general")

    # el admin como un ícono de sí/no
    @admin.display(boolean=True, description="Soporte vital OK")
    def soporte_vital_ok(self, obj):
        return obj.soporte_vital_ok
