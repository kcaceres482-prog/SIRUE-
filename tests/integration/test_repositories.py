"""Pruebas de integración para repositorios SQLAlchemy, el Contenedor y Autenticación UAB."""

from datetime import datetime, timedelta, timezone
import unittest
import uuid

from sqlalchemy.exc import IntegrityError

from sirue.application.dtos.reporte_dto import ReporteInputDTO
from sirue.application.dtos.usuario_dto import LoginInputDTO, RegistroUsuarioInputDTO
from sirue.domain.entities.coincidencia import Coincidencia, EstadoCoincidencia
from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.entities.usuario import RolUsuario, Usuario
from sirue.domain.exceptions.domain_exceptions import ValidacionError
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus
from sirue.infrastructure.container import Container
from sirue.infrastructure.persistence.database import Database
from sirue.infrastructure.persistence.repositories.sqlalchemy_coincidencia_repository import (
    SQLAlchemyCoincidenciaRepository,
)
from sirue.infrastructure.persistence.repositories.sqlalchemy_reporte_repository import (
    SQLAlchemyReporteRepository,
)
from sirue.infrastructure.persistence.repositories.sqlalchemy_usuario_repository import (
    SQLAlchemyUsuarioRepository,
)
from sirue.infrastructure.seeding import sembrar_usuarios_autorizados


class TestSQLAlchemyRepositories(unittest.TestCase):
    """Pruebas de integración sobre SQLite en memoria para adaptadores de persistencia."""

    def setUp(self) -> None:
        self.db = Database(db_url="sqlite:///:memory:")
        self.db.crear_tablas()
        self.session = self.db.SessionLocal()
        self.usuario_repo = SQLAlchemyUsuarioRepository(self.session)
        self.reporte_repo = SQLAlchemyReporteRepository(self.session)
        self.coincidencia_repo = SQLAlchemyCoincidenciaRepository(self.session)
        self.ahora = datetime.now(timezone.utc) - timedelta(hours=1)

    def tearDown(self) -> None:
        self.session.close()

    def test_persistencia_usuario(self) -> None:
        user_id = str(uuid.uuid4())
        usuario = Usuario(
            id=user_id,
            nombre="Carlos Estudiante",
            email="carlos@uab.edu.bo",
            telefono="3001234567",
        )
        self.usuario_repo.guardar(usuario)
        self.session.commit()

        recuperado = self.usuario_repo.obtener_por_id(user_id)
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.nombre, "Carlos Estudiante")
        self.assertEqual(recuperado.email, "carlos@uab.edu.bo")

        por_email = self.usuario_repo.obtener_por_email("carlos@uab.edu.bo")
        self.assertIsNotNone(por_email)
        self.assertEqual(por_email.id, user_id)

    def test_obtener_por_email_normalizado_insensible_mayusculas(self) -> None:
        user_id = str(uuid.uuid4())
        usuario = Usuario(
            id=user_id,
            nombre="Daniel Ramos",
            email="daniel.ramos@uab.edu.bo",
        )
        self.usuario_repo.guardar(usuario)
        self.session.commit()

        # Debe encontrar al usuario sin importar mayúsculas o espacios circundantes
        recuperado = self.usuario_repo.obtener_por_email("  DANIEL.RAMOS@UAB.EDU.BO  ")
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.id, user_id)
        self.assertEqual(recuperado.email, "daniel.ramos@uab.edu.bo")

    def test_persistencia_usuario_email_duplicado_lanza_error_integridad(self) -> None:
        u1 = Usuario(
            id=str(uuid.uuid4()),
            nombre="Usuario Uno",
            email="duplicado@uab.edu.bo",
        )
        self.usuario_repo.guardar(u1)
        self.session.commit()

        u2 = Usuario(
            id=str(uuid.uuid4()),
            nombre="Usuario Dos",
            email="duplicado@uab.edu.bo",
        )
        with self.assertRaises(IntegrityError):
            self.usuario_repo.guardar(u2)
        self.session.rollback()

    def test_persistencia_usuario_email_externo_rechazado_por_dominio(self) -> None:
        with self.assertRaises(ValidacionError):
            Usuario(
                id=str(uuid.uuid4()),
                nombre="Externo",
                email="externo@gmail.com",
            )

    def test_persistencia_usuario_con_rol_y_password(self) -> None:
        user_id = str(uuid.uuid4())
        usuario = Usuario(
            id=user_id,
            nombre="Admin Test",
            email="admin.test@uab.edu.bo",
            rol="admin",
            password_hash="pbkdf2_sha256$100000$salt$hash",
        )
        self.usuario_repo.guardar(usuario)
        self.session.commit()

        recuperado = self.usuario_repo.obtener_por_id(user_id)
        self.assertIsNotNone(recuperado)
        self.assertTrue(recuperado.es_admin())
        self.assertEqual(recuperado.password_hash, "pbkdf2_sha256$100000$salt$hash")

    def test_actualizar_usuario(self) -> None:
        user_id = str(uuid.uuid4())
        usuario = Usuario(
            id=user_id,
            nombre="Nombre Original",
            email="original@uab.edu.bo",
        )
        self.usuario_repo.guardar(usuario)
        self.session.commit()

        usuario.nombre = "Nombre Modificado"
        usuario.cambiar_rol("admin")
        self.usuario_repo.actualizar(usuario)
        self.session.commit()

        actualizado = self.usuario_repo.obtener_por_id(user_id)
        self.assertIsNotNone(actualizado)
        self.assertEqual(actualizado.nombre, "Nombre Modificado")
        self.assertTrue(actualizado.es_admin())

    def test_eliminar_usuario_elimina_reportes_en_cascada(self) -> None:
        user_id = str(uuid.uuid4())
        self.usuario_repo.guardar(
            Usuario(id=user_id, nombre="Usuario Cascada", email="cascada@uab.edu.bo")
        )
        rep_id = str(uuid.uuid4())
        self.reporte_repo.guardar(
            ReporteObjeto(
                id=rep_id,
                tipo=TipoReporte.PERDIDO,
                titulo="Objeto Cascada",
                descripcion="Descripcion del objeto",
                categoria=CategoriaObjeto.OTRO,
                ubicacion=UbicacionCampus(referencia_interna="Lab 1"),
                fecha_hora_incidente=FechaHoraIncidente(self.ahora),
                usuario_id=user_id,
            )
        )
        self.session.commit()

        # Eliminar usuario
        res = self.usuario_repo.eliminar(user_id)
        self.session.commit()
        self.assertTrue(res)

        # Verificar que el usuario y su reporte ya no existen
        self.assertIsNone(self.usuario_repo.obtener_por_id(user_id))
        self.assertIsNone(self.reporte_repo.obtener_por_id(rep_id))

    def test_persistencia_reporte(self) -> None:
        user_id = str(uuid.uuid4())
        self.usuario_repo.guardar(
            Usuario(id=user_id, nombre="Ana", email="ana@uab.edu.bo")
        )
        self.session.commit()

        rep_id = str(uuid.uuid4())
        reporte = ReporteObjeto(
            id=rep_id,
            tipo=TipoReporte.PERDIDO,
            titulo="Mochila Totto roja",
            descripcion="Mochila roja dejada en aula durante examen de fisica",
            categoria=CategoriaObjeto.MOCHILA,
            ubicacion=UbicacionCampus(referencia_interna="Aula A-203"),
            fecha_hora_incidente=FechaHoraIncidente(self.ahora),
            usuario_id=user_id,
        )
        self.reporte_repo.guardar(reporte)
        self.session.commit()

        recuperado = self.reporte_repo.obtener_por_id(rep_id)
        self.assertIsNotNone(recuperado)
        self.assertEqual(recuperado.titulo, "Mochila Totto roja")
        self.assertEqual(recuperado.categoria, CategoriaObjeto.MOCHILA)
        self.assertEqual(recuperado.ubicacion.referencia_interna, "Aula A-203")

        activos = self.reporte_repo.listar_activos_por_tipo(TipoReporte.PERDIDO)
        self.assertEqual(len(activos), 1)

        # Actualizar a resuelto
        recuperado.marcar_resuelto()
        self.reporte_repo.actualizar(recuperado)
        self.session.commit()

        activos_despues = self.reporte_repo.listar_activos_por_tipo(TipoReporte.PERDIDO)
        self.assertEqual(len(activos_despues), 0)

        # Test listar_todos y listar_por_estado
        todos = self.reporte_repo.listar_todos()
        self.assertEqual(len(todos), 1)

        resueltos = self.reporte_repo.listar_por_estado(EstadoReporte.RESUELTO)
        self.assertEqual(len(resueltos), 1)
        self.assertEqual(resueltos[0].id, rep_id)

    def test_persistencia_coincidencia(self) -> None:
        user_id = str(uuid.uuid4())
        self.usuario_repo.guardar(
            Usuario(id=user_id, nombre="Luis", email="luis@uab.edu.bo")
        )
        self.session.commit()

        p_id = str(uuid.uuid4())
        e_id = str(uuid.uuid4())

        self.reporte_repo.guardar(
            ReporteObjeto(
                id=p_id,
                tipo=TipoReporte.PERDIDO,
                titulo="Calculadora Casio",
                descripcion="Calculadora olvidada en mesa del laboratorio",
                categoria=CategoriaObjeto.OTRO,
                ubicacion=UbicacionCampus(referencia_interna="Lab 1"),
                fecha_hora_incidente=FechaHoraIncidente(self.ahora),
                usuario_id=user_id,
            )
        )
        self.reporte_repo.guardar(
            ReporteObjeto(
                id=e_id,
                tipo=TipoReporte.ENCONTRADO,
                titulo="Calculadora Casio encontrada",
                descripcion="Calculadora científica hallada en mesón",
                categoria=CategoriaObjeto.OTRO,
                ubicacion=UbicacionCampus(referencia_interna="Lab 1"),
                fecha_hora_incidente=FechaHoraIncidente(self.ahora),
                usuario_id=user_id,
            )
        )
        self.session.commit()

        c_id = str(uuid.uuid4())
        coincidencia = Coincidencia(
            id=c_id,
            reporte_perdido_id=p_id,
            reporte_encontrado_id=e_id,
            puntuacion=0.95,
            detalles={"categoria": 1.0, "espacio": 1.0, "tiempo": 1.0},
        )
        self.coincidencia_repo.guardar(coincidencia)
        self.session.commit()

        recuperada = self.coincidencia_repo.obtener_por_id(c_id)
        self.assertIsNotNone(recuperada)
        self.assertEqual(recuperada.puntuacion, 0.95)
        self.assertEqual(recuperada.estado, EstadoCoincidencia.PENDIENTE)
        self.assertTrue(self.coincidencia_repo.existe_coincidencia(p_id, e_id))


class TestContainerIntegration(unittest.TestCase):
    """Pruebas de ensamble e integración a través de Container."""

    def test_ensamble_casos_de_uso_con_container(self) -> None:
        container = Container(db_url="sqlite:///:memory:")
        container.init()

        with container.database.get_session() as session:
            # Crear usuario
            u_repo = container.usuario_repository(session)
            user_id = str(uuid.uuid4())
            u_repo.guardar(
                Usuario(id=user_id, nombre="Estudiante Demo", email="demo@uab.edu.bo")
            )
            session.commit()

            # Obtener casos de uso ensamblados desde el contenedor
            uc_perdido = container.registrar_objeto_perdido_use_case(session)
            ahora_iso = datetime.now(timezone.utc).isoformat()

            dto = ReporteInputDTO(
                titulo="Mochila Azul Totto",
                descripcion="Mochila dejada en la biblioteca piso tres mesa diez",
                categoria_str="MOCHILA",
                referencia="Biblioteca Piso 3",
                fecha_hora_str=ahora_iso,
                usuario_id=user_id,
            )
            out, matches = uc_perdido.ejecutar(dto)

            self.assertEqual(out.titulo, "Mochila Azul Totto")
            self.assertEqual(out.tipo, "PERDIDO")

    def test_ensamble_y_flujo_completo_auth_y_admin_con_container(self) -> None:
        container = Container(db_url="sqlite:///:memory:")
        container.init()

        with container.database.get_session() as session:
            uc_reg = container.registrar_usuario_use_case(session)
            uc_auth = container.autenticar_usuario_use_case(session)
            uc_admin = container.gestionar_reporte_admin_use_case(session)

            self.assertIsNotNone(uc_reg)
            self.assertIsNotNone(uc_auth)
            self.assertIsNotNone(uc_admin)

            # 1. Registrar usuario normal a través de use case ensamblado con container
            dto_reg = RegistroUsuarioInputDTO(
                nombre="Estudiante Nuevo",
                email="nuevo.estudiante@uab.edu.bo",
                password="passwordSegura123",
                confirm_password="passwordSegura123",
            )
            user_out = uc_reg.ejecutar(dto_reg, es_registro_publico=True)
            self.assertEqual(user_out.email, "nuevo.estudiante@uab.edu.bo")
            self.assertEqual(user_out.rol, "usuario")
            self.assertFalse(user_out.es_admin)

            # 2. Autenticarlo mediante el use case ensamblado
            auth_out = uc_auth.ejecutar(
                LoginInputDTO(
                    email="nuevo.estudiante@uab.edu.bo",
                    password="passwordSegura123",
                )
            )
            self.assertEqual(auth_out.id, user_out.id)
            self.assertFalse(auth_out.es_admin)

    def test_sembrado_usuarios_autorizados_con_container(self) -> None:
        container = Container(db_url="sqlite:///:memory:")
        container.init()

        # Ejecutar siembra autorizada institucional
        sembrar_usuarios_autorizados(container)

        with container.database.get_session() as session:
            uc_auth = container.autenticar_usuario_use_case(session)

            # Verificar que el administrador institucional existe y puede autenticarse
            admin = uc_auth.ejecutar(
                LoginInputDTO(
                    email="administrador@uab.edu.bo",
                    password="admin123",
                )
            )
            self.assertTrue(admin.es_admin)
            self.assertEqual(admin.rol, "admin")

            # Verificar que el estudiante institucional existe y puede autenticarse
            estudiante = uc_auth.ejecutar(
                LoginInputDTO(
                    email="estudiante@uab.edu.bo",
                    password="password123",
                )
            )
            self.assertFalse(estudiante.es_admin)
            self.assertEqual(estudiante.rol, "usuario")


if __name__ == "__main__":
    unittest.main()
