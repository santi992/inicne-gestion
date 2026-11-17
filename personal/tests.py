import os
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from acuicultura.models import ControlDiario
from equipamiento.models import Equipo, Movimiento
from tareas.models import Tarea

from .models import Persona


def ejecutar(comando, **opciones):
    """
    ejecuta un comando de manage.py y devuelve lo que imprimió
    """

    salida = StringIO()
    call_command(comando, stdout=salida, **opciones)
    return salida.getvalue()


class PrepararProduccionTests(TestCase):
    """
    el plan gratuito de Render no permite abrir una terminal
    el administrador se crea con este comando durante el despliegue
    """

    ENTORNO = {
        "DJANGO_SUPERUSER_USERNAME": "director",
        "DJANGO_SUPERUSER_PASSWORD": "una-clave-larga-123",
        "DJANGO_SUPERUSER_EMAIL": "director@ejemplo.com",
    }

    def test_crea_el_administrador_con_su_ficha_de_persona(self):
        # patch.dict simula las variables de entorno solo durante este bloque
        with mock.patch.dict(os.environ, self.ENTORNO):
            ejecutar("preparar_produccion")
        usuario = User.objects.get(username="director")
        self.assertTrue(usuario.is_superuser)
        self.assertTrue(usuario.check_password("una-clave-larga-123"))
        self.assertTrue(usuario.persona.es_administrador)

    def test_se_puede_ejecutar_varias_veces_sin_duplicar_ni_pisar_la_clave(self):
        with mock.patch.dict(os.environ, self.ENTORNO):
            ejecutar("preparar_produccion")
        with mock.patch.dict(
            os.environ, {**self.ENTORNO, "DJANGO_SUPERUSER_PASSWORD": "otra-clave-999"}
        ):
            salida = ejecutar("preparar_produccion")
        self.assertEqual(User.objects.filter(username="director").count(), 1)
        # no se cambia la contraseña de un usuario existente
        self.assertTrue(
            User.objects.get(username="director").check_password("una-clave-larga-123")
        )
        self.assertIn("ya existe", salida)

    def test_sin_variables_no_crea_nada_y_no_falla(self):
        entorno_vacio = {k: "" for k in self.ENTORNO}
        with mock.patch.dict(os.environ, entorno_vacio):
            ejecutar("preparar_produccion")
        self.assertEqual(User.objects.count(), 0)

    def test_carga_la_demo_solo_si_se_pide(self):
        with mock.patch.dict(os.environ, {"CARGAR_DEMO": ""}):
            ejecutar("preparar_produccion")
        self.assertEqual(Equipo.objects.count(), 0)
        with mock.patch.dict(os.environ, {"CARGAR_DEMO": "1"}):
            ejecutar("preparar_produccion")
        self.assertGreater(Equipo.objects.count(), 0)


class CargarDemoTests(TestCase):
    def test_carga_equipos_tareas_y_control_diario(self):
        ejecutar("cargar_demo")
        self.assertEqual(Equipo.objects.count(), 12)
        self.assertEqual(Persona.objects.count(), 5)
        self.assertEqual(ControlDiario.objects.count(), 2)

    def test_las_tareas_muestran_todos_los_niveles_de_alerta(self):
        ejecutar("cargar_demo")
        niveles = {t.nivel_alerta for t in Tarea.objects.all()}
        self.assertEqual(niveles, {"vencida", "por_vencer", "normal", "completada"})

    def test_hay_un_retiro_pendiente_y_otro_devuelto(self):
        ejecutar("cargar_demo")
        self.assertEqual(
            Movimiento.objects.filter(fecha_devolucion__isnull=True).count(), 1
        )
        self.assertEqual(
            Movimiento.objects.filter(fecha_devolucion__isnull=False).count(), 1
        )

    def test_el_control_diario_enlaza_con_una_tarea_de_mantenimiento(self):
        ejecutar("cargar_demo")
        con_problema = ControlDiario.objects.get(aireadores_ok=False)
        self.assertEqual(con_problema.tarea_mantenimiento.area, "SOP")
        self.assertFalse(con_problema.soporte_vital_ok)

    def test_no_duplica_si_ya_hay_datos(self):
        ejecutar("cargar_demo")
        salida = ejecutar("cargar_demo")
        self.assertEqual(Equipo.objects.count(), 12)
        self.assertEqual(Tarea.objects.count(), 11)
        self.assertIn("Ya hay", salida)

    def test_reiniciar_reemplaza_sin_duplicar(self):
        ejecutar("cargar_demo")
        ejecutar("cargar_demo", reiniciar=True)
        self.assertEqual(Equipo.objects.count(), 12)
        self.assertEqual(Tarea.objects.count(), 11)
        self.assertEqual(User.objects.filter(username__startswith="demo_").count(), 5)

    def test_sin_contrasena_demo_no_se_puede_iniciar_sesion(self):
        # un sitio público no puede tener usuarios con una contraseña conocida por defecto
        with mock.patch.dict(os.environ, {"DEMO_PASSWORD": ""}):
            ejecutar("cargar_demo")
        self.assertFalse(User.objects.get(username="demo_ana").has_usable_password())

    def test_con_contrasena_demo_se_puede_iniciar_sesion(self):
        with mock.patch.dict(os.environ, {"DEMO_PASSWORD": "demo-clave-123"}):
            ejecutar("cargar_demo")
        self.assertTrue(
            self.client.login(username="demo_ana", password="demo-clave-123")
        )
