import os
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from acuicultura.models import ControlDiario, Estanque, Lote
from equipamiento.models import Actividad, Categoria, Equipo, Movimiento, Ubicacion
from personal.models import Persona
from tareas.models import Proyecto, Tarea


class Command(BaseCommand):
    """
    carga datos de demostración para mostrar el sistema funcionando:
        equipos según Anexo I
        control según Anexo III
        tareas según Anexo IV

    las fechas se calculan a partir de HOY
    los usuarios empiezan con "demo_"

    python manage.py cargar_demo               (solo si la base está vacía)
    python manage.py cargar_demo --reiniciar   (borra todo y vuelve a cargar)

    los usuarios de demostración usan DEMO_PASSWORD
    si no existe, quedan sin contraseña y no se puede entrar con ellos
    """

    help = "Carga datos de demostración (equipos, tareas, control diario)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reiniciar",
            action="store_true",
            help="Borra equipos, tareas, proyectos y acuicultura, y carga todo de nuevo.",
        )

    # atomic para cargar todo o no cargar nada
    @transaction.atomic
    def handle(self, *args, **opciones):
        if opciones["reiniciar"]:
            self.borrar_datos()
        elif Equipo.objects.exists() or Tarea.objects.exists():
            self.stdout.write(
                "Ya hay equipos o tareas cargados: no se agrega nada. "
                "Usá --reiniciar para empezar de cero."
            )
            return

        self.password = os.environ.get("DEMO_PASSWORD")
        if not self.password:
            self.stdout.write(
                "Aviso: no hay DEMO_PASSWORD. Los usuarios demo se crean "
                "sin contraseña y no se podrá iniciar sesión con ellos."
            )

        personas = self.crear_personas()
        self.crear_equipamiento(personas)
        tareas = self.crear_tareas(personas)
        self.crear_acuicultura(personas, tareas)
        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados."))

    # ------------------------------------------------------------------
    def borrar_datos(self):
        # primero borra lo que depende de otra cosa
        # (los modelos usan PROTECT para no borrar algo que se usa)
        for modelo in (
            Movimiento,
            ControlDiario,
            Equipo,
            Lote,
            Estanque,
            Tarea,
            Proyecto,
        ):
            modelo.objects.all().delete()
        self.stdout.write("Datos anteriores borrados.")

    def crear_persona(
        self,
        usuario,
        nombre,
        apellido,
        area,
        rol=Persona.Rol.PERSONAL,
        cargo=Persona.Cargo.BECARIO,
    ):
        User = get_user_model()
        user, creado = User.objects.get_or_create(
            username=usuario, defaults={"first_name": nombre, "last_name": apellido}
        )
        if creado:
            if self.password:
                user.set_password(self.password)
            else:
                user.set_unusable_password()
            user.save()
        persona, _ = Persona.objects.get_or_create(
            usuario=user, defaults={"area": area, "rol": rol, "cargo": cargo}
        )
        return persona

    def crear_personas(self):
        # una persona por cada área del Anexo IV
        return {
            "admin": self.crear_persona(
                "demo_admin",
                "Coordinación",
                "General",
                "COORD",
                rol=Persona.Rol.ADMINISTRADOR,
                cargo=Persona.Cargo.DOCENTE,
            ),
            "ana": self.crear_persona("demo_ana", "Ana", "Producción", "PROD"),
            "marta": self.crear_persona(
                "demo_marta", "Marta", "Soporte", "SOP", cargo=Persona.Cargo.TECNICO
            ),
            "luis": self.crear_persona("demo_luis", "Luis", "Campo", "CAMPO"),
            "diego": self.crear_persona(
                "demo_diego",
                "Diego",
                "Investigación",
                "INV",
                cargo=Persona.Cargo.DOCENTE,
            ),
        }

    # ------------------------------------------------------------------
    def crear_equipamiento(self, personas):
        categorias = {
            n: Categoria.objects.get_or_create(nombre=n)[0]
            for n in ("Turbinas", "Redes", "Equipos de calidad", "Incubadoras")
        }
        sitios = {
            n: Ubicacion.objects.get_or_create(nombre=n)[0]
            for n in (
                "Casilla bombas arriba",
                "Casilla bombas abajo",
                "Depósito",
                "Sector B",
                "Sector C",
                "Sala de incubación",
            )
        }
        actividades = {
            n: Actividad.objects.get_or_create(nombre=n)[0]
            for n in ("Biometría", "Muestreo", "Mantenimiento")
        }

        O = Equipo.Estado.OPERATIVO
        RM = Equipo.Estado.REQUIERE_MANTENIMIENTO
        # (código, nombre, categoría, ubicación, estado)
        # ver Anexo I
        filas = [
            ("EQ-001-A", "Turbina 1,3 HP", "Turbinas", "Casilla bombas arriba", O),
            ("EQ-001-B", "Turbina 0,75 HP", "Turbinas", "Casilla bombas abajo", O),
            ("EQ-001-C", "Turbina 1,5 HP", "Turbinas", "Depósito", O),
            ("EQ-002-A", "Red grande 2 cm", "Redes", "Sector B", RM),
            ("EQ-002-B", "Red mediana 5 mm", "Redes", "Sector B", O),
            ("EQ-002-C", "Red chica 1 cm", "Redes", "Sector B", O),
            ("EQ-002-D", "Red chica 5 mm", "Redes", "Sector B", O),
            ("EQ-002-E", "Cuadro 5 mm", "Redes", "Sector B", O),
            (
                "EQ-003-A",
                "Equipo de calidad de agua 1",
                "Equipos de calidad",
                "Sector C",
                O,
            ),
            (
                "EQ-003-B",
                "Equipo de calidad de agua 2",
                "Equipos de calidad",
                "Sector C",
                O,
            ),
            ("EQ-004-A", "Incubadora 1", "Incubadoras", "Sala de incubación", O),
            ("EQ-004-B", "Incubadora 2", "Incubadoras", "Sala de incubación", O),
        ]
        hoy = timezone.localdate()
        equipos = {}
        for i, (codigo, nombre, cat, sitio, estado) in enumerate(filas):
            equipos[codigo] = Equipo.objects.create(
                codigo=codigo,
                nombre=nombre,
                categoria=categorias[cat],
                ubicacion=sitios[sitio],
                estado=estado,
                fecha_ultima_revision=hoy - timedelta(days=10 + i * 3),
                responsable=personas["marta"],
                observaciones="Revisar la malla" if estado == RM else "",
            )

        ahora = timezone.now()
        # un retiro que sigue pendiente de devolución
        Movimiento.objects.create(
            equipo=equipos["EQ-002-B"],
            persona_retira=personas["luis"],
            actividad=actividades["Muestreo"],
            fecha_retiro=ahora - timedelta(hours=5),
        )
        # un equipo ya devuelto
        Movimiento.objects.create(
            equipo=equipos["EQ-001-C"],
            persona_retira=personas["marta"],
            actividad=actividades["Mantenimiento"],
            fecha_retiro=ahora - timedelta(days=2),
            persona_devuelve=personas["marta"],
            fecha_devolucion=ahora - timedelta(days=2) + timedelta(hours=3),
            estado_devolucion="O",
            observaciones="Sin novedades",
        )

    # ------------------------------------------------------------------
    def crear_tareas(self, personas):
        hoy = timezone.localdate()
        P, C, H = Tarea.Estado.PENDIENTE, Tarea.Estado.EN_CURSO, Tarea.Estado.COMPLETADA
        ALTA, MEDIA, BAJA = (
            Tarea.Prioridad.ALTA,
            Tarea.Prioridad.MEDIA,
            Tarea.Prioridad.BAJA,
        )

        proyecto = Proyecto.objects.create(
            nombre="Producción de sábalo y pacú",
            director=personas["admin"],
            fecha_inicio=hoy - timedelta(days=60),
            observaciones="Meta anual: 1000 docenas de sabalitos y 10.000 juveniles de pacú.",
        )
        proyecto.colaboradores.set([personas["ana"], personas["luis"]])

        # (título, área, persona, días desde hoy, estado, prioridad, proyecto, descripción)
        # días negativos == tareas atrasadas
        # ver Anexo IV
        filas = [
            (
                "Reunión operativa semanal",
                "COORD",
                "admin",
                0,
                C,
                ALTA,
                None,
                "Planificación y diagnóstico: revisión general y definición de prioridades.",
            ),
            (
                "Definir prioridades de la campaña",
                "COORD",
                "admin",
                2,
                P,
                MEDIA,
                None,
                "",
            ),
            (
                "Alimentación y limpieza de estanques",
                "PROD",
                "ana",
                0,
                P,
                ALTA,
                proyecto,
                "",
            ),
            (
                "Clasificación y manejo de lotes",
                "PROD",
                "ana",
                1,
                P,
                MEDIA,
                proyecto,
                "",
            ),
            (
                "Mantenimiento preventivo de bombas",
                "SOP",
                "marta",
                -2,
                P,
                ALTA,
                None,
                "Bombas y aireadores. Quedó pendiente de la semana pasada.",
            ),
            ("Revisión de redes e incubadoras", "SOP", "marta", 3, P, MEDIA, None, ""),
            (
                "Visita a productores",
                "CAMPO",
                "luis",
                1,
                P,
                MEDIA,
                proyecto,
                "Seguimiento técnico en pisciculturas de la zona.",
            ),
            ("Muestreo de campo", "CAMPO", "luis", 10, P, BAJA, None, ""),
            (
                "Procesamiento de datos de biometría",
                "INV",
                "diego",
                4,
                C,
                MEDIA,
                proyecto,
                "",
            ),
            ("Informe semanal", "INV", "diego", 0, H, MEDIA, None, ""),
        ]
        tareas = {}
        for titulo, area, quien, dias, estado, prioridad, proy, desc in filas:
            # fecha de finalización se autocompleta al guardar
            tareas[titulo] = Tarea.objects.create(
                titulo=titulo,
                area=area,
                responsable=personas[quien],
                fecha_limite=hoy + timedelta(days=dias),
                estado=estado,
                prioridad=prioridad,
                proyecto=proy,
                descripcion=desc,
            )

        # una tarea de mantenimiento que "detectó" el control diario de acuicultura
        tareas["aireadores"] = Tarea.objects.create(
            titulo="Reparar aireador del Estanque 2",
            area="SOP",
            responsable=personas["marta"],
            fecha_limite=hoy - timedelta(days=1),
            estado=P,
            prioridad=ALTA,
            descripcion="Detectado en el control diario: aireador sin funcionar.",
        )
        return tareas

    # ------------------------------------------------------------------
    def crear_acuicultura(self, personas, tareas):
        hoy = timezone.localdate()
        e1 = Estanque.objects.create(
            nombre="Estanque 1", capacidad_litros=20000, especie_actual="Pacú"
        )
        e2 = Estanque.objects.create(
            nombre="Estanque 2", capacidad_litros=15000, especie_actual="Sábalo"
        )
        Lote.objects.create(
            especie="Pacú",
            cantidad=5000,
            estanque=e1,
            fecha_ingreso=hoy - timedelta(days=45),
        )
        Lote.objects.create(
            especie="Sábalo",
            cantidad=1200,
            estanque=e2,
            fecha_ingreso=hoy - timedelta(days=30),
        )

        T = ControlDiario.Turno.MANANA
        # Estanque 1: todo en orden
        ControlDiario.objects.create(
            fecha=hoy,
            turno=T,
            estanque=e1,
            responsable=personas["ana"],
            temperatura=Decimal("26.5"),
            oxigeno_disuelto=Decimal("6.20"),
            ph=Decimal("7.40"),
            conductividad=Decimal("310.0"),
            cantidad_alimento=Decimal("4.50"),
            estado_general=ControlDiario.EstadoGeneral.BUENO,
            mortalidad=0,
        )
        # Estanque 2: falla un aireador, el oxígeno está bajo y se generó una tarea
        ControlDiario.objects.create(
            fecha=hoy,
            turno=T,
            estanque=e2,
            responsable=personas["ana"],
            aireadores_ok=False,
            temperatura=Decimal("27.8"),
            oxigeno_disuelto=Decimal("3.10"),
            ph=Decimal("7.10"),
            conductividad=Decimal("335.0"),
            cantidad_alimento=Decimal("2.00"),
            estado_general=ControlDiario.EstadoGeneral.REGULAR,
            mortalidad=4,
            novedades="Aireador sin funcionar desde la madrugada.",
            tarea_mantenimiento=tareas["aireadores"],
        )
