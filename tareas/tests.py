from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from personal.models import Persona

from .models import Tarea


class TareasBase(TestCase):
    """Datos de partida compartidos: un administrador y dos personas del personal."""

    @classmethod
    def setUpTestData(cls):
        cls.hoy = timezone.localdate()
        u_admin = User.objects.create_user("admin1", password="clave123")
        cls.admin = Persona.objects.create(
            usuario=u_admin, area="COORD", rol=Persona.Rol.ADMINISTRADOR
        )
        u_ana = User.objects.create_user("ana", password="clave123")
        cls.ana = Persona.objects.create(usuario=u_ana, area="PROD")
        u_luis = User.objects.create_user("luis", password="clave123")
        cls.luis = Persona.objects.create(usuario=u_luis, area="CAMPO")

        # Una tarea de Ana y otra de Luis, las dos con fecha límite mañana
        cls.tarea_ana = Tarea.objects.create(
            titulo="Alimentar estanques", area="PROD",
            responsable=cls.ana, fecha_limite=cls.hoy + timedelta(days=1),
        )
        cls.tarea_luis = Tarea.objects.create(
            titulo="Visita a productor", area="CAMPO",
            responsable=cls.luis, fecha_limite=cls.hoy + timedelta(days=1),
        )

    def datos_tarea(self, **cambios):
        """Datos válidos para el formulario de tarea; cada prueba cambia lo que necesita."""
        datos = {
            "titulo": "Revisar bombas", "descripcion": "", "proyecto": "",
            "area": "SOP", "responsable": self.ana.pk,
            "fecha_limite": (self.hoy + timedelta(days=3)).isoformat(),
            "prioridad": "MEDIA",
        }
        datos.update(cambios)
        return datos


class PermisosCrearTareaTests(TareasBase):
    def test_personal_no_puede_crear_tareas(self):
        self.client.login(username="ana", password="clave123")
        # Ni abriendo el formulario...
        self.assertEqual(self.client.get(reverse("tareas:crear")).status_code, 403)
        # ...ni enviándolo a mano
        respuesta = self.client.post(reverse("tareas:crear"), self.datos_tarea())
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Tarea.objects.filter(titulo="Revisar bombas").exists())

    def test_administrador_crea_una_tarea(self):
        self.client.login(username="admin1", password="clave123")
        respuesta = self.client.post(reverse("tareas:crear"), self.datos_tarea())
        self.assertEqual(respuesta.status_code, 302)
        tarea = Tarea.objects.get(titulo="Revisar bombas")
        # Una tarea nueva siempre arranca pendiente
        self.assertEqual(tarea.estado, Tarea.Estado.PENDIENTE)

    def test_no_se_crea_una_tarea_con_fecha_pasada(self):
        self.client.login(username="admin1", password="clave123")
        ayer = (self.hoy - timedelta(days=1)).isoformat()
        respuesta = self.client.post(
            reverse("tareas:crear"), self.datos_tarea(fecha_limite=ayer)
        )
        self.assertEqual(respuesta.status_code, 200)  # vuelve a mostrar el formulario
        self.assertFalse(Tarea.objects.filter(titulo="Revisar bombas").exists())

    def test_personal_no_puede_editar_ni_eliminar(self):
        self.client.login(username="ana", password="clave123")
        self.assertEqual(
            self.client.get(reverse("tareas:editar", args=[self.tarea_ana.pk])).status_code, 403
        )
        self.assertEqual(
            self.client.post(reverse("tareas:eliminar", args=[self.tarea_ana.pk])).status_code, 403
        )
        self.assertTrue(Tarea.objects.filter(pk=self.tarea_ana.pk).exists())

    def test_administrador_elimina_una_tarea(self):
        self.client.login(username="admin1", password="clave123")
        self.client.post(reverse("tareas:eliminar", args=[self.tarea_luis.pk]))
        self.assertFalse(Tarea.objects.filter(pk=self.tarea_luis.pk).exists())


class CambiarEstadoTests(TareasBase):
    def cambiar(self, tarea, estado, **extra):
        return self.client.post(
            reverse("tareas:estado", args=[tarea.pk]), {"estado": estado, **extra}
        )

    def test_el_responsable_completa_su_tarea(self):
        self.client.login(username="ana", password="clave123")
        self.cambiar(self.tarea_ana, "HECHA")
        self.tarea_ana.refresh_from_db()
        self.assertEqual(self.tarea_ana.estado, "HECHA")
        # El save() del modelo anotó la fecha de finalización
        self.assertEqual(self.tarea_ana.fecha_completada, self.hoy)

    def test_otra_persona_no_puede_cambiar_una_tarea_ajena(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.cambiar(self.tarea_luis, "HECHA")
        self.assertEqual(respuesta.status_code, 403)
        self.tarea_luis.refresh_from_db()
        self.assertEqual(self.tarea_luis.estado, "PEND")

    def test_el_administrador_cambia_cualquier_tarea(self):
        self.client.login(username="admin1", password="clave123")
        self.cambiar(self.tarea_luis, "CURSO")
        self.tarea_luis.refresh_from_db()
        self.assertEqual(self.tarea_luis.estado, "CURSO")

    def test_un_estado_inventado_no_cambia_nada(self):
        self.client.login(username="ana", password="clave123")
        self.cambiar(self.tarea_ana, "INVENTADO")
        self.tarea_ana.refresh_from_db()
        self.assertEqual(self.tarea_ana.estado, "PEND")

    def test_reabrir_borra_la_fecha_de_finalizacion(self):
        self.client.login(username="ana", password="clave123")
        self.cambiar(self.tarea_ana, "HECHA")
        self.cambiar(self.tarea_ana, "PEND")
        self.tarea_ana.refresh_from_db()
        self.assertIsNone(self.tarea_ana.fecha_completada)

    def test_solo_acepta_post(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(reverse("tareas:estado", args=[self.tarea_ana.pk]))
        self.assertEqual(respuesta.status_code, 405)

    def test_next_externo_se_ignora(self):
        # Un sitio malicioso podría pedir que después del cambio se redirija a él
        self.client.login(username="ana", password="clave123")
        respuesta = self.cambiar(self.tarea_ana, "CURSO", next="https://sitio-malo.com/")
        self.assertRedirects(respuesta, reverse("tablero"))

    def test_next_propio_se_respeta(self):
        self.client.login(username="ana", password="clave123")
        destino = reverse("tablero") + "?vista=hoy"
        respuesta = self.cambiar(self.tarea_ana, "CURSO", next=destino)
        self.assertRedirects(respuesta, destino)

    def test_anonimo_no_puede_cambiar_estados(self):
        respuesta = self.cambiar(self.tarea_ana, "HECHA")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/ingresar/", respuesta.url)
        self.tarea_ana.refresh_from_db()
        self.assertEqual(self.tarea_ana.estado, "PEND")
