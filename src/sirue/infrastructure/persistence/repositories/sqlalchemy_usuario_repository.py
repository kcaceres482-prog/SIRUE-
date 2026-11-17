"""Implementación SQLAlchemy del repositorio de usuarios."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from sirue.domain.entities.usuario import Usuario
from sirue.domain.ports.usuario_repository import UsuarioRepository
from sirue.infrastructure.persistence.models.coincidencia_model import CoincidenciaModel
from sirue.infrastructure.persistence.models.reporte_model import ReporteModel
from sirue.infrastructure.persistence.models.usuario_model import UsuarioModel


class SQLAlchemyUsuarioRepository(UsuarioRepository):
    """Repositorio de usuarios respaldado por SQLAlchemy/SQLite."""

    def __init__(self, session: Session) -> None:
        """Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión activa de SQLAlchemy.
        """
        self._session = session

    def guardar(self, usuario: Usuario) -> Usuario:
        """Persiste un usuario en la base de datos.

        Args:
            usuario: Entidad Usuario a guardar.

        Returns:
            El usuario guardado.
        """
        modelo = UsuarioModel.from_entity(usuario)
        self._session.add(modelo)
        self._session.flush()
        return usuario

    def obtener_por_id(self, id: str) -> Optional[Usuario]:
        """Obtiene un usuario por su identificador.

        Args:
            id: Identificador único del usuario.

        Returns:
            El usuario encontrado o None.
        """
        modelo = self._session.get(UsuarioModel, id)
        if modelo is None:
            return None
        return modelo.to_entity()

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por su dirección de correo electrónico.

        Args:
            email: Correo electrónico del usuario.

        Returns:
            El usuario encontrado o None.
        """
        modelo = (
            self._session.query(UsuarioModel)
            .filter_by(email=email.lower().strip())
            .first()
        )
        if modelo is None:
            return None
        return modelo.to_entity()

    def listar_todos(self) -> list[Usuario]:
        """Obtiene todos los usuarios registrados.

        Returns:
            Lista de entidades Usuario.
        """
        modelos = self._session.query(UsuarioModel).all()
        return [m.to_entity() for m in modelos]

    def actualizar(self, usuario: Usuario) -> Usuario:
        """Actualiza un usuario existente en la base de datos.

        Args:
            usuario: Entidad Usuario con los datos actualizados.

        Returns:
            El usuario actualizado.
        """
        modelo = UsuarioModel.from_entity(usuario)
        self._session.merge(modelo)
        self._session.flush()
        return usuario

    def eliminar(self, id: str) -> bool:
        """Elimina un usuario y gestiona sus dependencias (reportes y coincidencias) en cascada.

        Args:
            id: Identificador único del usuario.

        Returns:
            True si fue eliminado, False si no existía.
        """
        modelo_usuario = self._session.get(UsuarioModel, id)
        if modelo_usuario is None:
            return False

        # 1. Obtener los IDs de todos los reportes del usuario
        reportes_usuario = (
            self._session.query(ReporteModel.id)
            .filter_by(usuario_id=id)
            .all()
        )
        reporte_ids = [r[0] for r in reportes_usuario]

        if reporte_ids:
            # 2. Eliminar coincidencias vinculadas a esos reportes
            self._session.query(CoincidenciaModel).filter(
                (CoincidenciaModel.reporte_perdido_id.in_(reporte_ids))
                | (CoincidenciaModel.reporte_encontrado_id.in_(reporte_ids))
            ).delete(synchronize_session=False)

            # 3. Eliminar los reportes del usuario
            self._session.query(ReporteModel).filter(
                ReporteModel.id.in_(reporte_ids)
            ).delete(synchronize_session=False)

        # 4. Eliminar el usuario
        self._session.delete(modelo_usuario)
        self._session.flush()
        return True
