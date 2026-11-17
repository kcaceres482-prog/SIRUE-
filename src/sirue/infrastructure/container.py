"""Contenedor de inyección de dependencias para la aplicación SIRUE."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from sirue.application.services.motor_coincidencias import MotorCoincidencias
from sirue.application.use_cases.autenticar_usuario import AutenticarUsuario
from sirue.application.use_cases.gestionar_reporte_admin import GestionarReporteAdmin
from sirue.application.use_cases.gestionar_usuario_admin import (
    CambiarEstadoUsuarioUseCase,
    CambiarRolUsuarioUseCase,
    EliminarUsuarioUseCase,
    ListarUsuariosAdminUseCase,
    RestablecerContrasenaUsuarioUseCase,
)
from sirue.application.use_cases.procesar_coincidencias import (
    ProcesarCoincidenciasYNotificar,
)
from sirue.application.use_cases.registrar_objeto_encontrado import (
    RegistrarObjetoEncontrado,
)
from sirue.application.use_cases.registrar_objeto_perdido import (
    RegistrarObjetoPerdido,
)
from sirue.application.use_cases.registrar_usuario import RegistrarUsuario
from sirue.infrastructure.notifications.in_app_notification_service import (
    InAppNotificationService,
)
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
from sirue.infrastructure.storage.local_photo_storage import LocalPhotoStorage


class Container:
    """Contenedor de Inversión de Control (IoC) e Inyección de Dependencias (DI).

    Responsable de instanciar y ensamblar los adaptadores de infraestructura
    y proporcionar los casos de uso con todas sus dependencias cableadas.
    """

    def __init__(
        self,
        db_url: str = "sqlite:///data/sirue.db",
        upload_path: str = "uploads",
    ) -> None:
        """Inicializa el contenedor con la configuración correspondiente.

        Args:
            db_url: URL de conexión a SQLite.
            upload_path: Directorio local para almacenamiento de fotografías.
        """
        self._database = Database(db_url=db_url)
        self._photo_storage = LocalPhotoStorage(base_path=upload_path)
        self._notification_service = InAppNotificationService()
        self._motor_coincidencias = MotorCoincidencias()

    def init(self) -> None:
        """Inicializa la base de datos y crea el esquema de tablas si no existe."""
        self._database.crear_tablas()

    # --- Acceso a infraestructura base ---

    @property
    def database(self) -> Database:
        """Gestor de base de datos."""
        return self._database

    @property
    def photo_storage(self) -> LocalPhotoStorage:
        """Adaptador de almacenamiento físico de fotos."""
        return self._photo_storage

    @property
    def notification_service(self) -> InAppNotificationService:
        """Adaptador singleton de notificaciones."""
        return self._notification_service

    @property
    def motor_coincidencias(self) -> MotorCoincidencias:
        """Servicio heurístico de afinidad y coincidencias."""
        return self._motor_coincidencias

    # --- Fábricas de Repositorios (inyectando Session) ---

    def usuario_repository(self, session: Session) -> SQLAlchemyUsuarioRepository:
        """Crea un repositorio de usuarios respaldado por la sesión indicada."""
        return SQLAlchemyUsuarioRepository(session)

    def reporte_repository(self, session: Session) -> SQLAlchemyReporteRepository:
        """Crea un repositorio de reportes respaldado por la sesión indicada."""
        return SQLAlchemyReporteRepository(session)

    def coincidencia_repository(
        self, session: Session
    ) -> SQLAlchemyCoincidenciaRepository:
        """Crea un repositorio de coincidencias respaldado por la sesión indicada."""
        return SQLAlchemyCoincidenciaRepository(session)

    # --- Fábricas de Casos de Uso Ensamblados ---

    def registrar_objeto_perdido_use_case(
        self, session: Session
    ) -> RegistrarObjetoPerdido:
        """Ensambla el caso de uso RegistrarObjetoPerdido con sus dependencias."""
        return RegistrarObjetoPerdido(
            reporte_repo=self.reporte_repository(session),
            usuario_repo=self.usuario_repository(session),
            coincidencia_repo=self.coincidencia_repository(session),
            motor_coincidencias=self._motor_coincidencias,
            notificacion_service=self._notification_service,
        )

    def registrar_objeto_encontrado_use_case(
        self, session: Session
    ) -> RegistrarObjetoEncontrado:
        """Ensambla el caso de uso RegistrarObjetoEncontrado con sus dependencias."""
        return RegistrarObjetoEncontrado(
            reporte_repo=self.reporte_repository(session),
            usuario_repo=self.usuario_repository(session),
            foto_storage=self._photo_storage,
            coincidencia_repo=self.coincidencia_repository(session),
            motor_coincidencias=self._motor_coincidencias,
            notificacion_service=self._notification_service,
        )

    def procesar_coincidencias_use_case(
        self, session: Session
    ) -> ProcesarCoincidenciasYNotificar:
        """Ensambla el caso de uso ProcesarCoincidenciasYNotificar con sus dependencias."""
        return ProcesarCoincidenciasYNotificar(
            coincidencia_repo=self.coincidencia_repository(session),
            reporte_repo=self.reporte_repository(session),
            usuario_repo=self.usuario_repository(session),
            motor_coincidencias=self._motor_coincidencias,
            notificacion_service=self._notification_service,
        )

    def autenticar_usuario_use_case(self, session: Session) -> AutenticarUsuario:
        """Ensambla el caso de uso AutenticarUsuario con sus dependencias."""
        return AutenticarUsuario(
            usuario_repo=self.usuario_repository(session),
        )

    def registrar_usuario_use_case(self, session: Session) -> RegistrarUsuario:
        """Ensambla el caso de uso RegistrarUsuario con sus dependencias."""
        return RegistrarUsuario(
            usuario_repo=self.usuario_repository(session),
        )

    def gestionar_reporte_admin_use_case(
        self, session: Session
    ) -> GestionarReporteAdmin:
        """Ensambla el caso de uso GestionarReporteAdmin con sus dependencias."""
        return GestionarReporteAdmin(
            reporte_repo=self.reporte_repository(session),
            usuario_repo=self.usuario_repository(session),
            coincidencia_repo=self.coincidencia_repository(session),
            notificacion_service=self._notification_service,
        )

    def restablecer_contrasena_usuario_use_case(
        self, session: Session
    ) -> RestablecerContrasenaUsuarioUseCase:
        """Ensambla el caso de uso RestablecerContrasenaUsuarioUseCase."""
        return RestablecerContrasenaUsuarioUseCase(
            usuario_repo=self.usuario_repository(session),
        )

    def cambiar_rol_usuario_use_case(
        self, session: Session
    ) -> CambiarRolUsuarioUseCase:
        """Ensambla el caso de uso CambiarRolUsuarioUseCase."""
        return CambiarRolUsuarioUseCase(
            usuario_repo=self.usuario_repository(session),
        )

    def cambiar_estado_usuario_use_case(
        self, session: Session
    ) -> CambiarEstadoUsuarioUseCase:
        """Ensambla el caso de uso CambiarEstadoUsuarioUseCase."""
        return CambiarEstadoUsuarioUseCase(
            usuario_repo=self.usuario_repository(session),
        )

    def eliminar_usuario_use_case(
        self, session: Session
    ) -> EliminarUsuarioUseCase:
        """Ensambla el caso de uso EliminarUsuarioUseCase."""
        return EliminarUsuarioUseCase(
            usuario_repo=self.usuario_repository(session),
        )

    def listar_usuarios_admin_use_case(
        self, session: Session
    ) -> ListarUsuariosAdminUseCase:
        """Ensambla el caso de uso ListarUsuariosAdminUseCase."""
        return ListarUsuariosAdminUseCase(
            usuario_repo=self.usuario_repository(session),
        )
