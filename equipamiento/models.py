from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from personal.models import Persona


class Categoria(models.Model):
    """tipo de equipo: turbinas, redes, incubadoras, control de calidad, etc"""

    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Ubicacion(models.Model):
    """
    lugar físico dentro del instituto donde se guarda un equipo
    (sector b, sala de incubación, depósito, etc)
    """

    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "ubicación"
        verbose_name_plural = "ubicaciones"

    def __str__(self):
        return self.nombre


class Actividad(models.Model):
    """actividad a realizarse que requiere un equipo (biometría, muestreo, etc)"""

    nombre = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "actividades"

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    """
    unidad física de equipamiento
    """

    # estados de equipo según indicaciones del cliente
    # ver Anexo I
    class Estado(models.TextChoices):
        OPERATIVO = "O", "Operativo"
        REQUIERE_MANTENIMIENTO = "RM", "Requiere mantenimiento"
        FUERA_DE_SERVICIO = "FS", "Fuera de servicio"
        BAJA = "B", "Baja"

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=120)
    # PROTECT no deja borrar una categoría o ubicación que todavía tiene equipos
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="equipos"
    )
    ubicacion = models.ForeignKey(
        Ubicacion, on_delete=models.PROTECT, related_name="equipos"
    )
    estado = models.CharField(
        max_length=2, choices=Estado.choices, default=Estado.OPERATIVO
    )
    # null=True: la columna puede quedar vacía en la base de datos
    # blank=True: el formulario deja enviar el campo vacío
    fecha_ultima_revision = models.DateField(null=True, blank=True)
    # SET_NULL: si se borra a la persona, el equipo queda sin responsable
    responsable = models.ForeignKey(
        Persona,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="equipos_a_cargo",
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Movimiento(models.Model):
    """
    registro de cada vez que alguien retira un equipo para una actividad
    """

    ESTADOS_DEVOLUCION = [
        (valor, etiqueta)
        for valor, etiqueta in Equipo.Estado.choices
        if valor != Equipo.Estado.BAJA
    ]

    equipo = models.ForeignKey(
        Equipo, on_delete=models.PROTECT, related_name="movimientos"
    )

    # persona que retira el equipo
    persona_retira = models.ForeignKey(
        Persona, on_delete=models.PROTECT, related_name="retiros"
    )
    # persona que devuelve el equipo
    persona_devuelve = models.ForeignKey(
        Persona,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="devoluciones",
    )
    actividad = models.ForeignKey(
        Actividad, on_delete=models.PROTECT, related_name="movimientos"
    )
    fecha_retiro = models.DateTimeField(default=timezone.now)
    fecha_devolucion = models.DateTimeField(null=True, blank=True)
    estado_devolucion = models.CharField(
        max_length=2, choices=ESTADOS_DEVOLUCION, blank=True
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        # oredena por fecha de más reciente a más antigua
        ordering = ["-fecha_retiro"]

    def __str__(self):
        return f"{self.equipo.codigo} retirado por {self.persona_retira}"

    @property
    def pendiente_devolucion(self):
        return self.fecha_devolucion is None

    def clean(self):
        # clean() se ejecuta al validar un formulario o desde el panel admin

        # comprobación de devolución correcta
        if self.fecha_devolucion:

            # comprobación de fechas
            if self.fecha_devolucion < self.fecha_retiro:
                raise ValidationError("La devolución no puede ser anterior al retiro.")

            # comprobación de registro de estado de la devolución
            if not self.estado_devolucion:
                raise ValidationError("Indicá en qué estado se devolvió el equipo.")

            # comprobación de registro de la persona que hace la devolución
            if not self.persona_devuelve:
                raise ValidationError("Indicá quién devuelve el equipo.")
