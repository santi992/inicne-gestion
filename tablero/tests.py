from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from personal.models import Persona
from tareas.models import Tarea


class TableroTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.hoy = timezone.localdate()
        u_ana = User.objects.create_user("ana", password="clave123")
        cls.ana = Persona.objects.create(usuario=u_ana, area="PROD")
        u_luis = User.objects.create_user("luis", password="clave123")
        cls.luis = Persona.objects.create(usuario=u_luis, area="CAMPO")

    def crear(self, titulo, dias, responsable=None, area="PROD", **extra):
        """Crea una tarea con fecha límite a "dias" días de hoy (negativo = pasado)."""
        return Tarea.objects.create(
            titulo=titulo, area=area, responsable=responsable or self.ana,
            fecha_limite=self.hoy + timedelta(days=dias), **extra
        )

    def titulos(self, **parametros):
        """Títulos que muestra el tablero para esos filtros."""
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(reverse("tablero"), parametros)
        return [t.titulo for t in respuesta.context["tareas"]]

    def test_anonimo_es_enviado_al_login(self):
        respuesta = self.client.get(reverse("tablero"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/ingresar/", respuesta.url)

    def test_inicio_lleva_al_tablero_si_hay_sesion(self):
        self.client.login(username="ana", password="clave123")
        self.assertRedirects(self.client.get(reverse("inicio")), reverse("tablero"))

    def test_el_personal_ve_tareas_de_otros(self):
        self.crear("De Luis", 0, responsable=self.luis)
        self.assertIn("De Luis", self.titulos())

    def test_vista_hoy_incluye_atrasadas_y_excluye_el_futuro(self):
        self.crear("Atrasada", -2)
        self.crear("De hoy", 0)
        self.crear("Lejana", 20)
        titulos = self.titulos(vista="hoy")
        self.assertIn("Atrasada", titulos)
        self.assertIn("De hoy", titulos)
        self.assertNotIn("Lejana", titulos)

    def test_la_semana_llega_hasta_el_domingo(self):
        # Calculo el domingo igual que la vista: weekday() es 0 el lunes, 6 el domingo
        domingo = (self.hoy + timedelta(days=6 - self.hoy.weekday())) - self.hoy
        self.crear("Vence el domingo", domingo.days)
        self.crear("Vence el lunes siguiente", domingo.days + 1)
        titulos = self.titulos(vista="semana")
        self.assertIn("Vence el domingo", titulos)
        self.assertNotIn("Vence el lunes siguiente", titulos)

    def test_vista_todas_incluye_lo_lejano(self):
        self.crear("Lejana", 20)
        self.assertNotIn("Lejana", self.titulos(vista="semana"))
        self.assertIn("Lejana", self.titulos(vista="todas"))

    def test_vista_invalida_usa_semana(self):
        self.crear("Lejana", 20)
        self.assertNotIn("Lejana", self.titulos(vista="cualquier-cosa"))

    def test_completada_hoy_sigue_visible(self):
        self.crear("Hecha hoy", 0, estado=Tarea.Estado.COMPLETADA)
        self.assertIn("Hecha hoy", self.titulos())

    def test_completada_ayer_ya_no_aparece(self):
        tarea = self.crear("Hecha ayer", 0, estado=Tarea.Estado.COMPLETADA)
        # update() evita pasar por save(), que pondría la fecha de hoy
        Tarea.objects.filter(pk=tarea.pk).update(
            fecha_completada=self.hoy - timedelta(days=1)
        )
        for vista in ("hoy", "semana", "todas"):
            self.assertNotIn("Hecha ayer", self.titulos(vista=vista))

    def test_solo_mis_tareas(self):
        self.crear("Mía", 0)
        self.crear("De Luis", 0, responsable=self.luis)
        titulos = self.titulos(mias="1")
        self.assertIn("Mía", titulos)
        self.assertNotIn("De Luis", titulos)

    def test_filtro_por_area(self):
        self.crear("De producción", 0, area="PROD")
        self.crear("De campo", 0, area="CAMPO", responsable=self.luis)
        titulos = self.titulos(area="CAMPO")
        self.assertEqual(titulos, ["De campo"])

    def test_contadores_de_alertas(self):
        self.crear("Vencida 1", -3)
        self.crear("Vencida 2", -1)
        self.crear("Por vencer", 1)
        self.crear("En plazo", 10)
        self.client.login(username="ana", password="clave123")
        contexto = self.client.get(reverse("tablero")).context
        self.assertEqual(contexto["n_vencidas"], 2)
        self.assertEqual(contexto["n_por_vencer"], 1)

    def test_etiqueta_verde_en_las_completadas(self):
        self.crear("Hecha hoy", 0, estado=Tarea.Estado.COMPLETADA)
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(reverse("tablero"))
        # #2e7d32 es el verde de COLORES_ALERTA["completada"]
        self.assertContains(respuesta, "#2e7d32")
