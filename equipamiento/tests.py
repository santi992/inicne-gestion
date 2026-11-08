from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from personal.models import Persona

from .models import Actividad, Categoria, Equipo, Movimiento, Ubicacion


class EquipamientoTests(TestCase):
    """
    pruebas automáticas de permisos y de la lógica de retiros y devoluciones.
    """

    @classmethod
    def setUpTestData(cls):
        # datos de partida, compartidos por todas las pruebas
        cls.user_admin = User.objects.create_user("admin1", password="clave123")
        Persona.objects.create(
            usuario=cls.user_admin, area="COORD", rol=Persona.Rol.ADMINISTRADOR
        )
        cls.user_ana = User.objects.create_user("ana", password="clave123")
        cls.ana = Persona.objects.create(usuario=cls.user_ana, area="PROD")

        cls.categoria = Categoria.objects.create(nombre="Turbinas")
        cls.ubicacion = Ubicacion.objects.create(nombre="Depósito")
        cls.actividad = Actividad.objects.create(nombre="Biometría")
        cls.equipo = Equipo.objects.create(
            codigo="EQ-001-A",
            nombre="Turbina 1,3 HP",
            categoria=cls.categoria,
            ubicacion=cls.ubicacion,
        )

    def test_anonimo_es_enviado_al_login(self):
        respuesta = self.client.get(reverse("equipamiento:lista"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/ingresar/", respuesta.url)

    def test_personal_puede_ver_el_listado(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(reverse("equipamiento:lista"))
        self.assertContains(respuesta, "EQ-001-A")

    def test_personal_no_puede_crear_equipos(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(reverse("equipamiento:crear"))
        self.assertEqual(respuesta.status_code, 403)

    def test_administrador_crea_un_equipo(self):
        self.client.login(username="admin1", password="clave123")
        respuesta = self.client.post(
            reverse("equipamiento:crear"),
            {
                "codigo": "EQ-002-A",
                "nombre": "Red grande 2 cm",
                "categoria": self.categoria.pk,
                "ubicacion": self.ubicacion.pk,
                "estado": "O",
                "fecha_ultima_revision": "",
                "responsable": "",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Equipo.objects.filter(codigo="EQ-002-A").exists())

    def test_retiro_queda_a_nombre_del_usuario_logueado(self):
        self.client.login(username="ana", password="clave123")
        self.client.post(
            reverse("equipamiento:retirar"),
            {
                "equipo": self.equipo.pk,
                "actividad": self.actividad.pk,
                "observaciones": "",
            },
        )
        movimiento = Movimiento.objects.get()
        self.assertEqual(movimiento.persona_retira, self.ana)
        self.assertTrue(movimiento.pendiente_devolucion)

    def test_equipo_retirado_no_se_puede_retirar_de_nuevo(self):
        Movimiento.objects.create(
            equipo=self.equipo, persona_retira=self.ana, actividad=self.actividad
        )
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.post(
            reverse("equipamiento:retirar"),
            {
                "equipo": self.equipo.pk,
                "actividad": self.actividad.pk,
                "observaciones": "",
            },
        )
        # si el formulario es inválido, Django no crea nada
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_equipo_fuera_de_servicio_no_se_puede_retirar(self):
        self.equipo.estado = Equipo.Estado.FUERA_DE_SERVICIO
        self.equipo.save()
        self.client.login(username="ana", password="clave123")
        self.client.post(
            reverse("equipamiento:retirar"),
            {
                "equipo": self.equipo.pk,
                "actividad": self.actividad.pk,
                "observaciones": "",
            },
        )
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_devolucion_actualiza_el_estado_del_equipo(self):
        movimiento = Movimiento.objects.create(
            equipo=self.equipo, persona_retira=self.ana, actividad=self.actividad
        )
        self.client.login(username="ana", password="clave123")
        self.client.post(
            reverse("equipamiento:devolver", args=[movimiento.pk]),
            {"estado_devolucion": "RM", "observaciones": "Hace ruido"},
        )
        movimiento.refresh_from_db()
        self.equipo.refresh_from_db()
        self.assertEqual(movimiento.persona_devuelve, self.ana)
        self.assertFalse(movimiento.pendiente_devolucion)
        self.assertEqual(self.equipo.estado, "RM")

    def test_movimiento_ya_devuelto_no_se_puede_devolver_otra_vez(self):
        movimiento = Movimiento.objects.create(
            equipo=self.equipo,
            persona_retira=self.ana,
            actividad=self.actividad,
            persona_devuelve=self.ana,
            fecha_devolucion="2026-01-01T10:00:00Z",
            estado_devolucion="O",
        )
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(
            reverse("equipamiento:devolver", args=[movimiento.pk])
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_equipo_con_historial_no_se_elimina(self):
        Movimiento.objects.create(
            equipo=self.equipo, persona_retira=self.ana, actividad=self.actividad
        )
        self.client.login(username="admin1", password="clave123")
        respuesta = self.client.post(
            reverse("equipamiento:eliminar", args=[self.equipo.pk])
        )
        # redirige con un mensaje y el equipo sigue existiendo
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Equipo.objects.filter(pk=self.equipo.pk).exists())

    def test_usuario_sin_persona_no_puede_retirar(self):
        User.objects.create_user("sinficha", password="clave123")
        self.client.login(username="sinficha", password="clave123")
        respuesta = self.client.get(reverse("equipamiento:retirar"))
        self.assertEqual(respuesta.status_code, 302)
