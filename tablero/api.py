from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from personal.models import AreaTrabajo
from personal.permisos import es_administrador, obtener_persona
from tareas.models import Tarea
from tareas.permisos import puede_cambiar_estado

from .consultas import contadores, filtrar_tareas
from .serializers import TareaSerializer


class ApiBase(APIView):
    """
    Configuración común de las dos vistas de la API. La pongo en cada vista
    en lugar de en settings.py para no tocar la configuración del proyecto.

    - SessionAuthentication: la API usa la MISMA sesión del login de Django.
      React corre en el mismo sitio, así que no hacen falta tokens aparte.
      Esta autenticación exige además el token CSRF en los POST.
    - IsAuthenticated: sin sesión iniciada, no se entrega ningún dato.
    - JSONRenderer: la API solo responde JSON.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]


class TableroAPIView(ApiBase):
    """
    GET /api/tablero/?vista=semana&area=PROD&mias=1

    Devuelve todo lo que React necesita para dibujar el tablero en una sola
    respuesta: quién es el usuario, los contadores y las tareas. Una sola
    consulta de red por actualización, en lugar de tres.
    """

    def get(self, request):
        persona = obtener_persona(request.user)
        # query_params es lo mismo que request.GET, pero con el nombre de DRF
        tareas, filtros = filtrar_tareas(request.query_params, persona)

        return Response({
            "usuario": {
                "nombre": request.user.get_full_name() or request.user.username,
                "es_admin": es_administrador(request.user),
                "persona_id": persona.pk if persona else None,
            },
            "filtros": filtros,
            "areas": [
                {"valor": valor, "etiqueta": etiqueta}
                for valor, etiqueta in AreaTrabajo.choices
            ],
            "contadores": contadores(),
            # many=True: serializa una lista de tareas, no una sola
            "tareas": TareaSerializer(tareas, many=True, context={"request": request}).data,
            "actualizado": timezone.localtime().isoformat(),
        })


class CambiarEstadoAPIView(ApiBase):
    """
    POST /api/tareas/<id>/estado/   con cuerpo {"estado": "HECHA"}

    Aplica las mismas reglas que la vista normal: solo el administrador o
    el responsable de la tarea pueden cambiarla, y el estado debe ser uno
    de los valores reales.
    """

    def post(self, request, pk):
        tarea = get_object_or_404(Tarea, pk=pk)

        if not puede_cambiar_estado(request.user, tarea):
            return Response(
                {"detalle": "No tenés permiso para cambiar esta tarea."},
                status=status.HTTP_403_FORBIDDEN,
            )

        nuevo_estado = request.data.get("estado", "")
        # Nunca confío en lo que manda el navegador: valido contra la lista real
        if nuevo_estado not in Tarea.Estado.values:
            return Response(
                {"detalle": "Estado no válido."}, status=status.HTTP_400_BAD_REQUEST
            )

        tarea.estado = nuevo_estado
        # El save() del modelo completa o borra fecha_completada solo
        tarea.save()
        return Response(TareaSerializer(tarea, context={"request": request}).data)
