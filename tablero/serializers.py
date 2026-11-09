from rest_framework import serializers

from personal.permisos import obtener_persona
from tareas.models import Tarea
from tareas.permisos import puede_cambiar_estado


class TareaSerializer(serializers.ModelSerializer):
    """
    Convierte una Tarea en el diccionario que se envía como JSON a React.
    Un serializer es el "traductor" entre el modelo de Django y el JSON:
    decide qué campos se exponen, y nada más sale de la API.

    Los campos de solo lectura se calculan en el servidor (alerta, colores,
    permisos). Así React no repite reglas de negocio: solo las muestra.
    """

    # StringRelatedField usa el __str__ del objeto relacionado (el nombre)
    proyecto = serializers.StringRelatedField()
    responsable_nombre = serializers.CharField(source="responsable", read_only=True)
    # source="get_area_display" llama a ese método del modelo y devuelve el texto
    area_display = serializers.CharField(source="get_area_display", read_only=True)
    prioridad_display = serializers.CharField(source="get_prioridad_display", read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    # Propiedades que definí en el modelo Tarea (día 2 y día 3)
    nivel_alerta = serializers.ReadOnlyField()
    etiqueta_alerta = serializers.ReadOnlyField()
    # Los métodos get_<campo> de abajo calculan estos campos
    color_fondo = serializers.SerializerMethodField()
    color_texto = serializers.SerializerMethodField()
    es_mia = serializers.SerializerMethodField()
    puede_cambiar_estado = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            "id", "titulo", "descripcion", "proyecto",
            "area", "area_display", "responsable_id", "responsable_nombre",
            "fecha_limite", "prioridad", "prioridad_display",
            "estado", "estado_display",
            "nivel_alerta", "etiqueta_alerta", "color_fondo", "color_texto",
            "es_mia", "puede_cambiar_estado",
        ]

    def get_color_fondo(self, tarea):
        return tarea.colores_alerta[0]

    def get_color_texto(self, tarea):
        return tarea.colores_alerta[1]

    def get_es_mia(self, tarea):
        # El contexto trae el pedido (request), y de ahí saco al usuario
        persona = obtener_persona(self.context["request"].user)
        return persona is not None and tarea.responsable_id == persona.pk

    def get_puede_cambiar_estado(self, tarea):
        # Le digo a React si mostrar los botones. Pero la decisión real la
        # vuelve a tomar el servidor al recibir el POST: ocultar un botón
        # no es seguridad, es comodidad.
        return puede_cambiar_estado(self.context["request"].user, tarea)
