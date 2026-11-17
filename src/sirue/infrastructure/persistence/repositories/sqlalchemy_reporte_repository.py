"""Implementación SQLAlchemy del repositorio de reportes."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.infrastructure.persistence.models.reporte_model import ReporteModel


class SQLAlchemyReporteRepository(ReporteRepository):
    """Repositorio de reportes de objetos respaldado por SQLAlchemy/SQLite."""

    def __init__(self, session: Session) -> None:
        """Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión activa de SQLAlchemy.
        """
        self._session = session

    def guardar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        """Persiste un reporte en la base de datos.

        Args:
            reporte: Entidad ReporteObjeto a guardar.

        Returns:
            El reporte guardado.
        """
        modelo = ReporteModel.from_entity(reporte)
        self._session.add(modelo)
        self._session.flush()
        return reporte

    def obtener_por_id(self, id: str) -> Optional[ReporteObjeto]:
        """Obtiene un reporte por su identificador.

        Args:
            id: Identificador único del reporte.

        Returns:
            El reporte encontrado o None.
        """
        modelo = self._session.get(ReporteModel, id)
        if modelo is None:
            return None
        return modelo.to_entity()

    def listar_todos(self) -> list[ReporteObjeto]:
        """Obtiene todos los reportes registrados sin filtro.

        Returns:
            Lista con todos los reportes.
        """
        modelos = self._session.query(ReporteModel).all()
        return [m.to_entity() for m in modelos]

    def listar_por_usuario(self, usuario_id: str) -> list[ReporteObjeto]:
        """Obtiene todos los reportes de un usuario específico.

        Args:
            usuario_id: Identificador del usuario.

        Returns:
            Lista de reportes del usuario.
        """
        modelos = (
            self._session.query(ReporteModel)
            .filter_by(usuario_id=usuario_id)
            .all()
        )
        return [m.to_entity() for m in modelos]

    def listar_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        """Obtiene todos los reportes de un tipo determinado.

        Args:
            tipo: Tipo de reporte (PERDIDO o ENCONTRADO).

        Returns:
            Lista de reportes del tipo indicado.
        """
        modelos = (
            self._session.query(ReporteModel)
            .filter_by(tipo=tipo.value)
            .all()
        )
        return [m.to_entity() for m in modelos]

    def listar_activos(self) -> list[ReporteObjeto]:
        """Obtiene todos los reportes con estado ACTIVO.

        Returns:
            Lista de reportes activos.
        """
        modelos = (
            self._session.query(ReporteModel)
            .filter_by(estado="ACTIVO")
            .all()
        )
        return [m.to_entity() for m in modelos]

    def listar_activos_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        """Obtiene todos los reportes activos de un tipo determinado.

        Args:
            tipo: Tipo de reporte (PERDIDO o ENCONTRADO).

        Returns:
            Lista de reportes activos del tipo indicado.
        """
        modelos = (
            self._session.query(ReporteModel)
            .filter(
                ReporteModel.estado == "ACTIVO",
                ReporteModel.tipo == tipo.value,
            )
            .all()
        )
        return [m.to_entity() for m in modelos]

    def listar_por_estado(self, estado: EstadoReporte) -> list[ReporteObjeto]:
        """Obtiene todos los reportes que tengan un estado específico.

        Args:
            estado: Estado del reporte (ACTIVO, EN_PROCESO, RECUPERADO, etc.).

        Returns:
            Lista de reportes con ese estado.
        """
        estado_val = estado.value if isinstance(estado, EstadoReporte) else str(estado)
        modelos = (
            self._session.query(ReporteModel)
            .filter_by(estado=estado_val)
            .all()
        )
        return [m.to_entity() for m in modelos]

    def actualizar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        """Actualiza un reporte existente en la base de datos.

        Args:
            reporte: Entidad ReporteObjeto con los datos actualizados.

        Returns:
            El reporte actualizado.
        """
        modelo = ReporteModel.from_entity(reporte)
        self._session.merge(modelo)
        self._session.flush()
        return reporte
