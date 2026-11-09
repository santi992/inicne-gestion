import json
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from personal.models import Persona
from tareas.models import Tarea


class ApiBase(TestCase):
    """Datos de partida: un administrador y dos personas del personal, con una tarea cada una."""

    @classmethod
    def setUpTestData(cls):
        cls.hoy = timezone.localdate()
        u_admin = User.objects.create_user("admin1", password="clave123")
        cls.admin = Persona.objects.create(
            usuario=u_admin, area="COORD", rol=Persona.Rol.ADMINISTRADOR
        )
        u_ana = User.objects.create_user("ana", first_name="Ana", last_name="Paz", password="clave123")
        cls.ana = Persona.objects.create(usuario=u_ana, area="PROD")
        u_luis = User.objects.create_user("luis", password="clave123")
        cls.luis = Persona.objects.create(usuario=u_luis, area="CAMPO")

        # Las dos vencen hoy: así siempre entran en la vista "semana",
        # sea cual sea el día de la semana en que se ejecute la prueba
        cls.tarea_ana = Tarea.objects.create(
            titulo="Alimentar estanques", area="PROD",
            responsable=cls.ana, fecha_limite=cls.hoy,
        )
        cls.tarea_luis = Tarea.objects.create(
            titulo="Visita a productor", area="CAMPO",
            responsable=cls.luis, fecha_limite=cls.hoy,
        )

    def obtener(self, **parametros):
        return self.client.get(reverse("api_tablero"), parametros)

    def cambiar_estado(self, tarea, estado, cliente=None):
        # Una API recibe JSON, no un formulario: por eso content_type
        return (cliente or self.client).post(
            reverse("api_tarea_estado", args=[tarea.pk]),
            data=json.dumps({"estado": estado}),
            content_type="application/json",
        )


class TableroAPITests(ApiBase):
    def test_sin_sesion_no_entrega_datos(self):
        respuesta = self.obtener()
        self.assertIn(respuesta.status_code, (401, 403))
        # Y lo importante: no se filtra ningún dato en la respuesta
        self.assertNotIn("Alimentar estanques", respuesta.content.decode())

    def test_estructura_de_la_respuesta(self):
        self.client.login(username="ana", password="clave123")
        datos = self.obtener().json()
        self.assertEqual(
            set(datos), {"usuario", "filtros", "areas", "contadores", "tareas", "actualizado"}
        )
        self.assertEqual(datos["usuario"]["nombre"], "Ana Paz")
        self.assertFalse(datos["usuario"]["es_admin"])
        self.assertEqual(datos["usuario"]["persona_id"], self.ana.pk)
        self.assertEqual(len(datos["areas"]), 5)

    def test_el_personal_ve_las_tareas_de_todos(self):
        self.client.login(username="ana", password="clave123")
        titulos = [t["titulo"] for t in self.obtener().json()["tareas"]]
        self.assertIn("Alimentar estanques", titulos)
        self.assertIn("Visita a productor", titulos)

    def test_cada_tarea_trae_alerta_y_colores_calculados_en_el_servidor(self):
        self.client.login(username="ana", password="clave123")
        tarea = next(t for t in self.obtener().json()["tareas"] if t["id"] == self.tarea_ana.pk)
        self.assertEqual(tarea["nivel_alerta"], "por_vencer")
        self.assertEqual(tarea["color_fondo"], "#f9a825")
        self.assertEqual(tarea["responsable_nombre"], "Ana Paz")
        self.assertEqual(tarea["fecha_limite"], self.hoy.isoformat())

    def test_completada_hoy_sale_en_verde(self):
        self.tarea_ana.estado = Tarea.Estado.COMPLETADA
        self.tarea_ana.save()
        self.client.login(username="ana", password="clave123")
        tarea = next(t for t in self.obtener().json()["tareas"] if t["id"] == self.tarea_ana.pk)
        self.assertEqual(tarea["color_fondo"], "#2e7d32")

    def test_los_filtros_funcionan_igual_que_en_el_tablero_clasico(self):
        self.client.login(username="ana", password="clave123")
        solo_mias = [t["titulo"] for t in self.obtener(mias="1").json()["tareas"]]
        self.assertEqual(solo_mias, ["Alimentar estanques"])
        solo_campo = [t["titulo"] for t in self.obtener(area="CAMPO").json()["tareas"]]
        self.assertEqual(solo_campo, ["Visita a productor"])

    def test_vista_y_area_invalidas_se_corrigen(self):
        self.client.login(username="ana", password="clave123")
        filtros = self.obtener(vista="inventada", area="inventada").json()["filtros"]
        self.assertEqual(filtros, {"vista": "semana", "area": "", "mias": False})

    def test_los_contadores_miran_a_todo_el_instituto(self):
        Tarea.objects.create(
            titulo="Atrasada", area="PROD", responsable=self.luis,
            fecha_limite=self.hoy - timedelta(days=3),
        )
        self.client.login(username="ana", password="clave123")
        contadores = self.obtener(mias="1").json()["contadores"]
        # Con el filtro "mias" activo, el contador de vencidas igual cuenta la de Luis
        self.assertEqual(contadores["vencidas"], 1)

    def test_banderas_de_permiso_para_los_botones(self):
        self.client.login(username="ana", password="clave123")
        tareas = {t["id"]: t for t in self.obtener().json()["tareas"]}
        self.assertTrue(tareas[self.tarea_ana.pk]["puede_cambiar_estado"])
        self.assertTrue(tareas[self.tarea_ana.pk]["es_mia"])
        self.assertFalse(tareas[self.tarea_luis.pk]["puede_cambiar_estado"])
        self.assertFalse(tareas[self.tarea_luis.pk]["es_mia"])

    def test_el_administrador_puede_cambiar_cualquier_tarea(self):
        self.client.login(username="admin1", password="clave123")
        datos = self.obtener().json()
        self.assertTrue(datos["usuario"]["es_admin"])
        self.assertTrue(all(t["puede_cambiar_estado"] for t in datos["tareas"]))


class CambiarEstadoAPITests(ApiBase):
    def test_el_responsable_completa_su_tarea(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.cambiar_estado(self.tarea_ana, "HECHA")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["estado"], "HECHA")
        self.tarea_ana.refresh_from_db()
        self.assertEqual(self.tarea_ana.fecha_completada, self.hoy)

    def test_no_se_puede_cambiar_una_tarea_ajena(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.cambiar_estado(self.tarea_luis, "HECHA")
        self.assertEqual(respuesta.status_code, 403)
        self.tarea_luis.refresh_from_db()
        self.assertEqual(self.tarea_luis.estado, "PEND")

    def test_el_administrador_cambia_cualquier_tarea(self):
        self.client.login(username="admin1", password="clave123")
        self.assertEqual(self.cambiar_estado(self.tarea_luis, "CURSO").status_code, 200)
        self.tarea_luis.refresh_from_db()
        self.assertEqual(self.tarea_luis.estado, "CURSO")

    def test_estado_inventado_devuelve_400(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.cambiar_estado(self.tarea_ana, "INVENTADO")
        self.assertEqual(respuesta.status_code, 400)
        self.tarea_ana.refresh_from_db()
        self.assertEqual(self.tarea_ana.estado, "PEND")

    def test_tarea_inexistente_devuelve_404(self):
        self.client.login(username="admin1", password="clave123")
        respuesta = self.client.post(
            reverse("api_tarea_estado", args=[99999]),
            data=json.dumps({"estado": "HECHA"}), content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_sin_sesion_no_se_puede_cambiar(self):
        respuesta = self.cambiar_estado(self.tarea_ana, "HECHA")
        self.assertIn(respuesta.status_code, (401, 403))
        self.tarea_ana.refresh_from_db()
        self.assertEqual(self.tarea_ana.estado, "PEND")

    def test_exige_token_csrf(self):
        # Por defecto el cliente de pruebas NO comprueba el CSRF. Este lo comprueba,
        # como hace un navegador real. Un POST sin el token debe rechazarse.
        cliente = Client(enforce_csrf_checks=True)
        cliente.login(username="ana", password="clave123")
        respuesta = self.cambiar_estado(self.tarea_ana, "HECHA", cliente=cliente)
        self.assertEqual(respuesta.status_code, 403)
        self.tarea_ana.refresh_from_db()
        self.assertEqual(self.tarea_ana.estado, "PEND")

    def test_con_token_csrf_valido_funciona(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.login(username="ana", password="clave123")
        # La página de React entrega la cookie csrftoken; la leo igual que React
        token = cliente.get(reverse("tablero_en_vivo")).cookies["csrftoken"].value
        respuesta = cliente.post(
            reverse("api_tarea_estado", args=[self.tarea_ana.pk]),
            data=json.dumps({"estado": "HECHA"}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(respuesta.status_code, 200)

    def test_solo_acepta_post(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(reverse("api_tarea_estado", args=[self.tarea_ana.pk]))
        self.assertEqual(respuesta.status_code, 405)


class PaginaEnVivoTests(ApiBase):
    def test_anonimo_es_enviado_al_login(self):
        respuesta = self.client.get(reverse("tablero_en_vivo"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/ingresar/", respuesta.url)

    def test_la_pagina_aloja_react_y_entrega_la_cookie_csrf(self):
        self.client.login(username="ana", password="clave123")
        respuesta = self.client.get(reverse("tablero_en_vivo"))
        self.assertContains(respuesta, 'id="root"')
        self.assertContains(respuesta, "tablero/react/tablero.js")
        self.assertIn("csrftoken", respuesta.cookies)
