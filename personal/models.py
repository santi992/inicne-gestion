from django.conf import settings
from django.db import models

# áreas de trabajo según pedido del cliente
# ver Anexo IV (Cronograma Semanal Operativo)


# TextChoices es una clase de Django que arma las opciones de un campo:
# el primer valor se guarda en la base de datos y el segundo es el que se muestra.
class AreaTrabajo(models.TextChoices):
    COORDINACION = "COORD", "Coordinación general"
    PRODUCCION = "PROD", "Producción"
    SOPORTE = "SOP", "Soporte"
    CAMPO = "CAMPO", "Campo"
    INVESTIGACION = "INV", "Investigación"


class Persona(models.Model):
    """
    una persona que trabaja en el instituto.
    """

    class Rol(models.TextChoices):
        ADMINISTRADOR = "ADMIN", "Administrador"
        PERSONAL = "PERSONAL", "Personal registrado"

    class Cargo(models.TextChoices):
        DOCENTE = "DOCENTE", "Docente"
        BECARIO = "BECARIO", "Becario"
        TECNICO = "TECNICO", "Técnico"
        OTRO = "OTRO", "Otro"

    # 1 a 1: cada User tiene como máximo una Persona y viceversa
    # CASCADE: si se borra el usuario, se borra también su ficha de persona
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="persona",
    )
    area = models.CharField(max_length=10, choices=AreaTrabajo.choices)
    cargo = models.CharField(
        max_length=10, choices=Cargo.choices, default=Cargo.BECARIO
    )
    rol = models.CharField(max_length=10, choices=Rol.choices, default=Rol.PERSONAL)
    telefono = models.CharField(max_length=30, blank=True)
    # en vez de borrar a alguien que se fue, lo marco como inactivo
    # para no perder el historial de tareas y movimientos que tuvo
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["usuario__last_name", "usuario__first_name"]
        verbose_name = "persona"
        verbose_name_plural = "personas"

    def __str__(self):
        # si np tiene cargados nombre y apellido, se muestra el nombre de usuario
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def es_administrador(self):
        # el superusuario que crea Django también cuenta como administrador
        return self.rol == self.Rol.ADMINISTRADOR or self.usuario.is_superuser
