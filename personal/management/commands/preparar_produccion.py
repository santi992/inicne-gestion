import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from personal.models import Persona


class Command(BaseCommand):
    """
    Deja el sitio listo para usar después de un despliegue. Se ejecuta solo
    en cada despliegue de Render (está en el buildCommand de render.yaml).

    Existe porque el plan gratuito de Render NO permite abrir una terminal
    en el servidor: no puedo escribir "createsuperuser" a mano. Entonces
    el administrador se crea acá, con datos que vienen de variables de entorno.

    Es seguro ejecutarlo muchas veces (es "idempotente"): si el administrador
    ya existe no lo toca, y los datos de demostración solo se cargan si la
    base está vacía.
    """

    help = "Crea el administrador y, si se pide, los datos de demostración."

    def handle(self, *args, **opciones):
        self.crear_administrador()
        self.cargar_demostracion()

    def crear_administrador(self):
        # Los tres datos salen del entorno, nunca del código
        usuario = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        clave = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        correo = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")

        if not usuario or not clave:
            self.stdout.write(
                "Sin DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD: "
                "no se crea ningún administrador."
            )
            return

        User = get_user_model()
        if User.objects.filter(username=usuario).exists():
            # no pisa la contraseña de un usuario que ya existe
            self.stdout.write(
                f"El administrador «{usuario}» ya existe. No se modifica."
            )
            return

        admin = User.objects.create_superuser(usuario, correo, clave)
        # crea la ficha de Persona del administrador
        Persona.objects.get_or_create(
            usuario=admin,
            defaults={
                "area": "COORD",
                "rol": Persona.Rol.ADMINISTRADOR,
                "cargo": Persona.Cargo.OTRO,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Administrador «{usuario}» creado."))

    def cargar_demostracion(self):
        modo = os.environ.get("CARGAR_DEMO", "").strip().lower()
        if modo in ("1", "true", "si", "sí"):
            call_command("cargar_demo")
        elif modo == "reiniciar":
            # borra y vuelve a cargar los datos de demostración
            call_command("cargar_demo", reiniciar=True)
        else:
            self.stdout.write(
                "CARGAR_DEMO no está activado: no se cargan datos de demostración."
            )
