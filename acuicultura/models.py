from django.db import models

from django.utils import timezone

from personal.models import Persona
from tareas.models import Tarea


class Estanque(models.Model):
    """
    un estanque o sistema de cultivo del instituto
    """

    nombre = models.CharField(max_length=80, unique=True)
    capacidad_litros = models.PositiveIntegerField(
        null=True, blank=True, help_text="Capacidad en litros"
    )
    especie_actual = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Lote(models.Model):
    """
    un grupo de peces de una misma especie que entra al instituto
    """

    especie = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField()
    # si el estanque se borra, el lote sigue existiendo, pero sin estanque
    estanque = models.ForeignKey(
        Estanque,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lotes",
    )
    fecha_ingreso = models.DateField(default=timezone.localdate)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-fecha_ingreso"]

    def __str__(self):
        return f"{self.especie} x{self.cantidad}"


class ControlDiario(models.Model):
    """
    checklist diario de tareas
    """

    class Turno(models.TextChoices):
        MANANA = "M", "Mañana"
        TARDE = "T", "Tarde"

    class EstadoGeneral(models.TextChoices):
        BUENO = "BUENO", "Bueno"
        REGULAR = "REG", "Regular"
        MALO = "MALO", "Malo"

    # --- Datos generales del control ---
    fecha = models.DateField(default=timezone.localdate)
    turno = models.CharField(max_length=1, choices=Turno.choices)
    estanque = models.ForeignKey(
        Estanque, on_delete=models.PROTECT, related_name="controles"
    )
    responsable = models.ForeignKey(
        Persona, on_delete=models.PROTECT, related_name="controles_realizados"
    )

    # --- 1. Sistemas de soporte vital ---
    # casilla tildada == funciona bien
    # el usuario destilda solo lo que encuentra fallando.
    aireadores_ok = models.BooleanField("Aireadores operativos", default=True)
    bombas_ok = models.BooleanField("Bombas funcionando", default=True)
    flujo_agua_ok = models.BooleanField("Flujo de agua correcto", default=True)
    energia_ok = models.BooleanField("Energía eléctrica normal", default=True)
    alarmas_ok = models.BooleanField("Alarmas y contingencias", default=True)

    # --- 2. Calidad de agua ---
    # max_digits == dígitos en total
    # decimal_places == cuántos dígitos hay después de la coma.
    temperatura = models.DecimalField(
        "Temperatura (°C)", max_digits=4, decimal_places=1, null=True, blank=True
    )
    oxigeno_disuelto = models.DecimalField(
        "Oxígeno disuelto (mg/L)",
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )
    ph = models.DecimalField(
        "pH", max_digits=4, decimal_places=2, null=True, blank=True
    )
    conductividad = models.DecimalField(
        "Conductividad (µS/cm)",
        max_digits=7,
        decimal_places=1,
        null=True,
        blank=True,
    )

    # --- 3. Alimentación ---
    hora_alimentacion = models.TimeField(null=True, blank=True)
    cantidad_alimento = models.DecimalField(
        "Cantidad de alimento (kg)",
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # --- 4. Estado de los lotes del estanque ---
    estado_general = models.CharField(
        max_length=5, choices=EstadoGeneral.choices, default=EstadoGeneral.BUENO
    )
    mortalidad = models.PositiveIntegerField(
        default=0, help_text="Cantidad de ejemplares muertos"
    )

    # --- 5. Mantenimiento detectado ---
    # si se detecta un problema se crea una Tarea normal (con prioridad y responsable) y se enlaza aquí
    # los problemas aparecen en el tablero y disparan alertas por sí mismos
    tarea_mantenimiento = models.ForeignKey(
        Tarea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="controles_origen",
    )

    # --- 6. Novedades del día ---
    novedades = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha", "estanque"]
        verbose_name_plural = "controles diarios"
        constraints = [
            # evita cargar dos veces el mismo estanque, el mismo día y turno
            models.UniqueConstraint(
                fields=["fecha", "estanque", "turno"],
                name="un_control_por_estanque_dia_y_turno",
            )
        ]

    def __str__(self):
        return f"{self.estanque} - {self.fecha} ({self.get_turno_display()})"

    @property
    def soporte_vital_ok(self):
        # all() da True solamente si las cinco casillas están tildadas
        return all(
            [
                self.aireadores_ok,
                self.bombas_ok,
                self.flujo_agua_ok,
                self.energia_ok,
                self.alarmas_ok,
            ]
        )
