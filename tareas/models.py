from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone

from personal.models import AreaTrabajo, Persona

# cuántos días antes del vencimiento una tarea pasa a estar "por vencer"
# uso una constante para cambiarlo desde un solo lugar
DIAS_ALERTA = 2

# color de cada nivel de alerta
# junto al modelo para que el panel admin y el tablero los mismos colores
COLORES_ALERTA = {
    "completada": ("#2e7d32", "#ffffff"),  # verde
    "vencida": ("#c62828", "#ffffff"),  # rojo
    "por_vencer": ("#f9a825", "#000000"),  # amarillo
    "normal": ("#e0e0e0", "#000000"),  # gris
}

# Texto que se muestra al usuario para cada nivel
ETIQUETAS_ALERTA = {
    "completada": "Completada",
    "vencida": "Vencida",
    "por_vencer": "Por vencer",
    "normal": "En plazo",
}


class Proyecto(models.Model):
    """
    un proyecto de investigación del instituto
    agrupa tareas
    """

    nombre = models.CharField(max_length=150)
    # cada proyecto tiene UN director (clave foránea)
    director = models.ForeignKey(
        Persona, on_delete=models.PROTECT, related_name="proyectos_dirigidos"
    )
    # puede tener VARIOS colaboradores
    # una persona puede colaborar en varios proyectos
    colaboradores = models.ManyToManyField(
        Persona, blank=True, related_name="proyectos_colaborados"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return self.nombre


class TareaQuerySet(models.QuerySet):
    """
    consultas reutilizables sobre tareas
    se usan encadenadas, por ejemplo: tarea.objects.pendientes().vencidas()
    las pongo en el modelo y no en las vistas para no repetir la lógica
    """

    def pendientes(self):
        # exclude saca las completadas y todo lo demás sigue "abierto"
        return self.exclude(estado=Tarea.Estado.COMPLETADA)

    def vencidas(self):
        # lt == "less than": fecha límite ya pasada y sin completar
        return self.pendientes().filter(fecha_limite__lt=timezone.localdate())

    def por_vencer(self):
        hoy = timezone.localdate()
        limite = hoy + timedelta(days=DIAS_ALERTA)
        # range == rango desde hoy hasta hoy + DIAS_ALERTA
        return self.pendientes().filter(fecha_limite__range=(hoy, limite))

    def visibles_en_tablero(self):
        """
        Las tareas que el tablero debe mostrar:
        todas las que siguen abiertas, más las que se completaron en el día
        """
        hoy = timezone.localdate()
        # Q para combinar condiciones con | y &
        abiertas = Q(estado__in=[Tarea.Estado.PENDIENTE, Tarea.Estado.EN_CURSO])
        completadas_hoy = Q(estado=Tarea.Estado.COMPLETADA, fecha_completada=hoy)
        return self.filter(abiertas | completadas_hoy)

    def de_hoy(self):
        return self.filter(fecha_limite=timezone.localdate())

    def de_la_semana(self):
        hoy = timezone.localdate()
        lunes = hoy - timedelta(days=hoy.weekday())
        domingo = lunes + timedelta(days=6)
        return self.filter(fecha_limite__range=(lunes, domingo))


class Tarea(models.Model):
    """
    una tarea asignada a una persona, con fecha límite y estado
    es el CORAZÓN del tablero
    """

    class Estado(models.TextChoices):
        PENDIENTE = "PEND", "Pendiente"
        EN_CURSO = "CURSO", "En curso"
        COMPLETADA = "HECHA", "Completada"

    # prioridades de tareas según el cliente
    # ver Anexo III
    class Prioridad(models.TextChoices):
        ALTA = "ALTA", "Alta"
        MEDIA = "MEDIA", "Media"
        BAJA = "BAJA", "Baja"

    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    # una tarea puede no pertenecer a ningún proyecto (por ejemplo, limpieza)
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tareas",
    )
    area = models.CharField(max_length=10, choices=AreaTrabajo.choices)
    # PROTECT para NO borrar a una persona que tiene tareas asignadas
    responsable = models.ForeignKey(
        Persona, on_delete=models.PROTECT, related_name="tareas"
    )
    fecha_limite = models.DateField()
    estado = models.CharField(
        max_length=5, choices=Estado.choices, default=Estado.PENDIENTE
    )
    prioridad = models.CharField(
        max_length=5, choices=Prioridad.choices, default=Prioridad.MEDIA
    )
    # editable=False: se autocompleta al guardar
    fecha_completada = models.DateField(null=True, blank=True, editable=False)
    # auto_now_add: Django guarda automáticamente la fecha de creación
    creada = models.DateTimeField(auto_now_add=True)

    # Conecto el QuerySet de arriba para poder usar Tarea.objects.vencidas()
    objects = TareaQuerySet.as_manager()

    class Meta:
        ordering = ["fecha_limite", "titulo"]

    def __str__(self):
        return f"{self.titulo} ({self.responsable})"

    def save(self, *args, **kwargs):
        # antes de guardar, controlo la fecha de finalización:

        # si la tarea se completó, guardo la fecha actual
        if self.estado == self.Estado.COMPLETADA:
            if not self.fecha_completada:
                self.fecha_completada = timezone.localdate()

        # si la tarea se reabrió, borro la fecha
        else:
            self.fecha_completada = None
        super().save(*args, **kwargs)

    @property
    def nivel_alerta(self):
        """
        dice en qué situación está la tarea
        el tablero usa este valor para pintarla de un color:
        'vencida' (rojo),
        'por_vencer' (amarillo),
        'normal',
        'completada' (verde)
        """
        if self.estado == self.Estado.COMPLETADA:
            return "completada"
        hoy = timezone.localdate()
        if self.fecha_limite < hoy:
            return "vencida"
        if self.fecha_limite <= hoy + timedelta(days=DIAS_ALERTA):
            return "por_vencer"
        return "normal"

    @property
    def colores_alerta(self):
        # busca en el diccionario los colores del nivel actual
        return COLORES_ALERTA[self.nivel_alerta]

    @property
    def etiqueta_alerta(self):
        return ETIQUETAS_ALERTA[self.nivel_alerta]
