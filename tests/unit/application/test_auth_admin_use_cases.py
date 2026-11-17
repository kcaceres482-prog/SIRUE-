"""Pruebas unitarias para Casos de Uso de Autenticación, Roles y Gestión Administrativa (UAB)."""

from datetime import datetime, timezone
from typing import Any, Optional
import unittest
import uuid

from sirue.application.dtos.usuario_dto import (
    LoginInputDTO,
    RegistroUsuarioInputDTO,
)
from sirue.application.services.password_hasher import PasswordHasher
from sirue.application.use_cases.autenticar_usuario import AutenticarUsuario
from sirue.application.use_cases.gestionar_reporte_admin import GestionarReporteAdmin
from sirue.application.use_cases.gestionar_usuario_admin import (
    CambiarEstadoUsuarioUseCase,
    CambiarRolUsuarioUseCase,
    EliminarUsuarioUseCase,
    ListarUsuariosAdminUseCase,
    RestablecerContrasenaUsuarioUseCase,
)
from sirue.application.use_cases.registrar_usuario import RegistrarUsuario
from sirue.domain.entities.coincidencia import Coincidencia, EstadoCoincidencia
from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.entities.usuario import RolUsuario, Usuario
from sirue.domain.exceptions.domain_exceptions import (
    AccesoDenegadoError,
    CredencialesInvalidasError,
    CuentaBloqueadaError,
    EmailYaRegistradoError,
    OperacionNoPermitidaError,
    ReporteNoEncontradoError,
    UsuarioNoEncontradoError,
    ValidacionError,
)
from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.domain.ports.usuario_repository import UsuarioRepository
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus


class InMemoryUsuarioRepo(UsuarioRepository):
    def __init__(self) -> None:
        self.usuarios: dict[str, Usuario] = {}

    def guardar(self, usuario: Usuario) -> Usuario:
        self.usuarios[usuario.id] = usuario
        return usuario

    def obtener_por_id(self, id: str) -> Optional[Usuario]:
        return self.usuarios.get(id)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        for u in self.usuarios.values():
            if u.email == email.lower().strip():
                return u
        return None

    def listar_todos(self) -> list[Usuario]:
        return list(self.usuarios.values())

    def actualizar(self, usuario: Usuario) -> Usuario:
        self.usuarios[usuario.id] = usuario
        return usuario

    def eliminar(self, id: str) -> bool:
        if id in self.usuarios:
            del self.usuarios[id]
            return True
        return False


class InMemoryReporteRepo(ReporteRepository):
    def __init__(self) -> None:
        self.reportes: dict[str, ReporteObjeto] = {}

    def guardar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        self.reportes[reporte.id] = reporte
        return reporte

    def obtener_por_id(self, id: str) -> Optional[ReporteObjeto]:
        return self.reportes.get(id)

    def listar_todos(self) -> list[ReporteObjeto]:
        return list(self.reportes.values())

    def listar_por_usuario(self, usuario_id: str) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.usuario_id == usuario_id]

    def listar_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.tipo == tipo]

    def listar_activos(self) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.esta_activo()]

    def listar_activos_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.esta_activo() and r.tipo == tipo]

    def listar_por_estado(self, estado: EstadoReporte) -> list[ReporteObjeto]:
        return [r for r in self.reportes.values() if r.estado == estado]

    def actualizar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        self.reportes[reporte.id] = reporte
        return reporte


class InMemoryCoincidenciaRepo(CoincidenciaRepository):
    def __init__(self) -> None:
        self.coincidencias: dict[str, Coincidencia] = {}

    def guardar(self, coincidencia: Coincidencia) -> Coincidencia:
        self.coincidencias[coincidencia.id] = coincidencia
        return coincidencia

    def obtener_por_id(self, id: str) -> Optional[Coincidencia]:
        return self.coincidencias.get(id)

    def listar_por_reporte(self, reporte_id: str) -> list[Coincidencia]:
        return [
            c for c in self.coincidencias.values()
            if c.reporte_perdido_id == reporte_id or c.reporte_encontrado_id == reporte_id
        ]

    def listar_pendientes(self) -> list[Coincidencia]:
        return [c for c in self.coincidencias.values() if c.estado == EstadoCoincidencia.PENDIENTE]

    def actualizar(self, coincidencia: Coincidencia) -> Coincidencia:
        self.coincidencias[coincidencia.id] = coincidencia
        return coincidencia

    def existe_coincidencia(self, perdido_id: str, encontrado_id: str) -> bool:
        return any(
            c.reporte_perdido_id == perdido_id and c.reporte_encontrado_id == encontrado_id
            for c in self.coincidencias.values()
        )


class TestPasswordHasher(unittest.TestCase):
    def test_hashear_y_verificar(self) -> None:
        raw = "miPasswordSeguro123"
        h = PasswordHasher.hashear_password(raw)
        self.assertTrue(h.startswith("pbkdf2_sha256$"))
        self.assertTrue(PasswordHasher.verificar_password(raw, h))
        self.assertFalse(PasswordHasher.verificar_password("otraPassword", h))

    def test_verificar_formato_invalido(self) -> None:
        self.assertFalse(PasswordHasher.verificar_password("algo", "formato_no_valido"))


class TestAutenticacionYRegistro(unittest.TestCase):
    def setUp(self) -> None:
        self.usuario_repo = InMemoryUsuarioRepo()
        self.uc_registro = RegistrarUsuario(self.usuario_repo)
        self.uc_auth = AutenticarUsuario(self.usuario_repo)

    # 1. Registro con correo institucional válido
    def test_registro_usuario_exitoso(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Carlos Gomez",
            email="carlos@uab.edu.bo",
            password="password123",
            confirm_password="password123",
            telefono="3001234567",
            rol="usuario",
        )
        res = self.uc_registro.ejecutar(dto)
        self.assertEqual(res.nombre, "Carlos Gomez")
        self.assertEqual(res.email, "carlos@uab.edu.bo")
        self.assertEqual(res.telefono, "3001234567")
        self.assertEqual(res.rol, "usuario")
        self.assertFalse(res.es_admin)

    def test_registro_telefono_con_espacios_y_guiones_se_normaliza(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Maria Lopez",
            email="maria.lopez@uab.edu.bo",
            password="password123",
            confirm_password="password123",
            telefono="+591 712-34567",
        )
        res = self.uc_registro.ejecutar(dto)
        self.assertEqual(res.telefono, "+59171234567")

    def test_registro_telefono_demasiado_corto_falla(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Pedro Perez",
            email="pedro.perez@uab.edu.bo",
            password="password123",
            confirm_password="password123",
            telefono="12345",  # Menos de 8 dígitos
        )
        with self.assertRaises(ValidacionError) as ctx:
            self.uc_registro.ejecutar(dto)
        self.assertIn("al menos 8 dígitos", str(ctx.exception))

    # 2. Rechazo de correos externos
    def test_registro_rechazo_correos_externos(self) -> None:
        correos_externos = [
            "usuario@gmail.com",
            "usuario@hotmail.com",
            "usuario@outlook.com",
            "usuario@uab.com",
            "usuario@campus.edu",
        ]
        for email_externo in correos_externos:
            dto = RegistroUsuarioInputDTO(
                nombre="Estudiante Externo",
                email=email_externo,
                password="password123",
            )
            with self.assertRaises(ValidacionError) as ctx:
                self.uc_registro.ejecutar(dto)
            self.assertIn("Solo se permiten correos institucionales con dominio @uab.edu.bo", str(ctx.exception))

    # 3. Rechazo de correos mal formados
    def test_registro_rechazo_correos_malformados(self) -> None:
        malformados = ["sin_arroba", "@uab.edu.bo", "usuario@@uab.edu.bo", ""]
        for email_mal in malformados:
            dto = RegistroUsuarioInputDTO(
                nombre="Estudiante Test",
                email=email_mal,
                password="password123",
            )
            with self.assertRaises(ValidacionError):
                self.uc_registro.ejecutar(dto)

    # 4. Rechazo de correos duplicados
    def test_registro_duplicado_falla(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Carlos Gomez",
            email="carlos@uab.edu.bo",
            password="password123",
        )
        self.uc_registro.ejecutar(dto)
        with self.assertRaises(EmailYaRegistradoError):
            self.uc_registro.ejecutar(dto)

    # 5. Rechazo de contraseñas que no coinciden
    def test_registro_contrasenas_no_coinciden_falla(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Ana Ramos",
            email="ana.ramos@uab.edu.bo",
            password="password123",
            confirm_password="otraPasswordDiferente",
        )
        with self.assertRaises(ValidacionError) as ctx:
            self.uc_registro.ejecutar(dto)
        self.assertIn("Las contraseñas no coinciden", str(ctx.exception))

    def test_registro_password_corta_falla(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Carlos",
            email="carlos@uab.edu.bo",
            password="123",
        )
        with self.assertRaises(ValidacionError):
            self.uc_registro.ejecutar(dto)

    # 11. Imposibilidad de asignarse privilegios administrativos mediante el registro público
    def test_imposibilidad_asignarse_admin_en_registro_publico(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Hacker Intruso",
            email="hacker@uab.edu.bo",
            password="password123",
            confirm_password="password123",
            rol="admin",
        )
        with self.assertRaises(AccesoDenegadoError) as ctx:
            self.uc_registro.ejecutar(dto, es_registro_publico=True)
        self.assertIn("No está permitido asignarse privilegios administrativos", str(ctx.exception))

    def test_registro_publico_por_defecto_asigna_rol_usuario(self) -> None:
        dto = RegistroUsuarioInputDTO(
            nombre="Laura Estudiante",
            email="laura@uab.edu.bo",
            password="password123",
            confirm_password="password123",
            rol="usuario",
        )
        res = self.uc_registro.ejecutar(dto, es_registro_publico=True)
        self.assertEqual(res.rol, "usuario")
        self.assertFalse(res.es_admin)

    # 6. Inicio de sesión con credenciales correctas
    def test_login_exitoso(self) -> None:
        # Administrador autorizado
        self.uc_registro.ejecutar(
            RegistroUsuarioInputDTO(
                nombre="Administrador UAB",
                email="administrador@uab.edu.bo",
                password="adminSecretPassword",
                rol="admin",
            )
        )

        res = self.uc_auth.ejecutar(
            LoginInputDTO(email="administrador@uab.edu.bo", password="adminSecretPassword")
        )
        self.assertEqual(res.email, "administrador@uab.edu.bo")
        self.assertEqual(res.rol, "admin")
        self.assertTrue(res.es_admin)

    # 7. Rechazo de credenciales incorrectas
    def test_login_credenciales_invalidas(self) -> None:
        self.uc_registro.ejecutar(
            RegistroUsuarioInputDTO(
                nombre="Usuario Test",
                email="test@uab.edu.bo",
                password="passwordValida",
            )
        )

        # Contraseña incorrecta
        with self.assertRaises(CredencialesInvalidasError):
            self.uc_auth.ejecutar(
                LoginInputDTO(email="test@uab.edu.bo", password="passwordEquivocada")
            )

        # Usuario institucional inexistente
        with self.assertRaises(CredencialesInvalidasError):
            self.uc_auth.ejecutar(
                LoginInputDTO(email="noexiste@uab.edu.bo", password="cualquiera")
            )

    def test_login_rechazo_correo_externo(self) -> None:
        with self.assertRaises(ValidacionError) as ctx:
            self.uc_auth.ejecutar(
                LoginInputDTO(email="usuario@gmail.com", password="password123")
            )
        self.assertIn("Solo se permiten correos institucionales con dominio @uab.edu.bo", str(ctx.exception))


class TestGestionReporteAdmin(unittest.TestCase):
    def setUp(self) -> None:
        self.usuario_repo = InMemoryUsuarioRepo()
        self.reporte_repo = InMemoryReporteRepo()
        self.coincidencia_repo = InMemoryCoincidenciaRepo()
        self.uc_admin = GestionarReporteAdmin(
            reporte_repo=self.reporte_repo,
            usuario_repo=self.usuario_repo,
            coincidencia_repo=self.coincidencia_repo,
        )

        # 8. Acceso diferenciado según el rol: Crear Admin y Estudiante
        self.admin = Usuario(
            id="admin-001",
            nombre="Admin UAB",
            email="administrador@uab.edu.bo",
            rol=RolUsuario.ADMIN,
        )
        self.usuario_repo.guardar(self.admin)

        self.estudiante = Usuario(
            id="est-001",
            nombre="Estudiante UAB",
            email="estudiante@uab.edu.bo",
            rol=RolUsuario.USUARIO,
        )
        self.usuario_repo.guardar(self.estudiante)

        # Crear Reporte
        self.reporte = ReporteObjeto(
            id="rep-001",
            tipo=TipoReporte.PERDIDO,
            titulo="Billetera de cuero",
            descripcion="Billetera negra perdida cerca de cafeteria",
            categoria=CategoriaObjeto.CARTERA,
            ubicacion=UbicacionCampus(referencia_interna="Cafetería Central"),
            fecha_hora_incidente=FechaHoraIncidente(datetime.now(timezone.utc)),
            usuario_id=self.estudiante.id,
        )
        self.reporte_repo.guardar(self.reporte)

    # 8. Acceso diferenciado: Estudiante no tiene privilegios de administración
    def test_no_admin_lanza_acceso_denegado(self) -> None:
        with self.assertRaises(AccesoDenegadoError):
            self.uc_admin.cambiar_estado_reporte("rep-001", "RECUPERADO", self.estudiante.id)

        with self.assertRaises(AccesoDenegadoError):
            self.uc_admin.listar_reportes_supervision(self.estudiante.id)

        with self.assertRaises(AccesoDenegadoError):
            self.uc_admin.obtener_estadisticas_globales(self.estudiante.id)

    def test_cambiar_estado_reporte_por_admin(self) -> None:
        res = self.uc_admin.cambiar_estado_reporte("rep-001", "RECUPERADO", self.admin.id)
        self.assertEqual(res.estado, "RECUPERADO")

        # Verificar persistencia
        rep_db = self.reporte_repo.obtener_por_id("rep-001")
        self.assertIsNotNone(rep_db)
        self.assertEqual(rep_db.estado, EstadoReporte.RECUPERADO)

    def test_estadisticas_globales_admin(self) -> None:
        stats = self.uc_admin.obtener_estadisticas_globales(self.admin.id)
        self.assertEqual(stats["total_reportes"], 1)
        self.assertEqual(stats["total_usuarios"], 2)
        self.assertEqual(stats["usuarios_admin"], 1)
        self.assertEqual(stats["usuarios_estudiantes"], 1)


class TestGestionUsuariosAdmin(unittest.TestCase):
    """Pruebas unitarias para los casos de uso de administración de usuarios."""

    def setUp(self) -> None:
        self.usuario_repo = InMemoryUsuarioRepo()
        self.hasher = PasswordHasher()

        # Admin
        self.admin = Usuario(
            id="admin-001",
            nombre="Admin Principal",
            email="admin.principal@uab.edu.bo",
            rol=RolUsuario.ADMIN,
            password_hash=self.hasher.hashear_password("AdminClave123*"),
            activo=True,
        )
        self.usuario_repo.guardar(self.admin)

        # Usuario normal
        self.usuario = Usuario(
            id="user-002",
            nombre="Carlos Estudiante",
            email="carlos.estudiante@uab.edu.bo",
            rol=RolUsuario.USUARIO,
            password_hash=self.hasher.hashear_password("PasswordVieja123"),
            activo=True,
        )
        self.usuario_repo.guardar(self.usuario)

        # Casos de uso
        self.uc_clave = RestablecerContrasenaUsuarioUseCase(self.usuario_repo)
        self.uc_rol = CambiarRolUsuarioUseCase(self.usuario_repo)
        self.uc_estado = CambiarEstadoUsuarioUseCase(self.usuario_repo)
        self.uc_eliminar = EliminarUsuarioUseCase(self.usuario_repo)
        self.uc_listar = ListarUsuariosAdminUseCase(self.usuario_repo)
        self.uc_auth = AutenticarUsuario(self.usuario_repo)

    def test_restablecer_contrasena_por_admin_exitoso(self) -> None:
        out = self.uc_clave.ejecutar(
            usuario_id=self.usuario.id,
            nueva_contrasena="NuevaClave2026*",
            admin_id=self.admin.id,
        )
        self.assertEqual(out.id, self.usuario.id)

        # Verificar que puede loguearse con la nueva contraseña
        auth_out = self.uc_auth.ejecutar(
            LoginInputDTO(email=self.usuario.email, password="NuevaClave2026*")
        )
        self.assertEqual(auth_out.id, self.usuario.id)

    def test_restablecer_contrasena_corta_falla(self) -> None:
        with self.assertRaises(ValidacionError):
            self.uc_clave.ejecutar(
                usuario_id=self.usuario.id,
                nueva_contrasena="123",
                admin_id=self.admin.id,
            )

    def test_cambiar_rol_usuario_a_admin_y_viceversa(self) -> None:
        # Ascender a admin
        out1 = self.uc_rol.ejecutar(self.admin.id, self.usuario.id, "admin")
        self.assertTrue(out1.es_admin)
        self.assertEqual(out1.rol, "admin")

        # Degradar a usuario
        out2 = self.uc_rol.ejecutar(self.admin.id, self.usuario.id, "usuario")
        self.assertFalse(out2.es_admin)
        self.assertEqual(out2.rol, "usuario")

    def test_autoproteccion_admin_no_puede_degradarse(self) -> None:
        with self.assertRaises(OperacionNoPermitidaError):
            self.uc_rol.ejecutar(self.admin.id, self.admin.id, "usuario")

    def test_bloquear_usuario_y_rechazo_en_login(self) -> None:
        # Bloquear usuario
        out = self.uc_estado.ejecutar(self.admin.id, self.usuario.id, activo=False)
        self.assertFalse(out.activo)

        # Intentar login debe lanzar CuentaBloqueadaError
        with self.assertRaises(CuentaBloqueadaError):
            self.uc_auth.ejecutar(
                LoginInputDTO(email=self.usuario.email, password="PasswordVieja123")
            )

    def test_desbloquear_usuario_y_restauracion_login(self) -> None:
        # Bloquear y luego desbloquear
        self.uc_estado.ejecutar(self.admin.id, self.usuario.id, activo=False)
        out = self.uc_estado.ejecutar(self.admin.id, self.usuario.id, activo=True)
        self.assertTrue(out.activo)

        # Ahora el login debe ser exitoso
        auth_out = self.uc_auth.ejecutar(
            LoginInputDTO(email=self.usuario.email, password="PasswordVieja123")
        )
        self.assertEqual(auth_out.id, self.usuario.id)

    def test_autoproteccion_admin_no_puede_bloquearse(self) -> None:
        with self.assertRaises(OperacionNoPermitidaError):
            self.uc_estado.ejecutar(self.admin.id, self.admin.id, activo=False)

    def test_eliminar_usuario_exitoso(self) -> None:
        eliminado = self.uc_eliminar.ejecutar(self.admin.id, self.usuario.id)
        self.assertTrue(eliminado)
        self.assertIsNone(self.usuario_repo.obtener_por_id(self.usuario.id))

    def test_autoproteccion_admin_no_puede_eliminarse(self) -> None:
        with self.assertRaises(OperacionNoPermitidaError):
            self.uc_eliminar.ejecutar(self.admin.id, self.admin.id)

    def test_no_admin_lanza_acceso_denegado_en_gestion_usuarios(self) -> None:
        with self.assertRaises(AccesoDenegadoError):
            self.uc_clave.ejecutar(self.usuario.id, "ClaveTest123", admin_id=self.usuario.id)

        with self.assertRaises(AccesoDenegadoError):
            self.uc_rol.ejecutar(self.usuario.id, self.admin.id, "usuario")

        with self.assertRaises(AccesoDenegadoError):
            self.uc_estado.ejecutar(self.usuario.id, self.admin.id, activo=False)

        with self.assertRaises(AccesoDenegadoError):
            self.uc_eliminar.ejecutar(self.usuario.id, self.admin.id)

        with self.assertRaises(AccesoDenegadoError):
            self.uc_listar.ejecutar(self.usuario.id)


if __name__ == "__main__":
    unittest.main()
