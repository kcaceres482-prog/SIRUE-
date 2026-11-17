"""Implementación SQLAlchemy del repositorio de coincidencias."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from sirue.domain.entities.coincidencia import Coincidencia
from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.infrastructure.persistence.models.coincidencia_model import (
    CoincidenciaModel,
)


class SQLAlchemyCoincidenciaRepository(CoincidenciaRepository):
    """Repositorio de coincidencias respaldado por SQLAlchemy/SQLite."""

    def __init__(self, session: Session) -> None:
        """Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión activa de SQLAlchemy.
        """
        self._session = session

    def guardar(self, coincidencia: Coincidencia) -> Coincidencia:
        """Persiste una coincidencia en la base de datos.

        Args:
            coincidencia: Entidad Coincidencia a guardar.

        Returns:
            La coincidencia guardada.
        """
        modelo = CoincidenciaModel.from_entity(coincidencia)
        self._session.add(modelo)
        self._session.flush()
        return coincidencia

    def obtener_por_id(self, id: str) -> Optional[Coincidencia]:
        """Obtiene una coincidencia por su identificador.

        Args:
            id: Identificador único de la coincidencia.

        Returns:
            La coincidencia encontrada o None.
        """
        modelo = self._session.get(CoincidenciaModel, id)
        if modelo is None:
            return None
        return modelo.to_entity()

    def listar_por_reporte(self, reporte_id: str) -> list[Coincidencia]:
        """Obtiene todas las coincidencias asociadas a un reporte.

        Args:
            reporte_id: Identificador del reporte (perdido o encontrado).

        Returns:
            Lista de coincidencias del reporte.
        """
        modelos = (
            self._session.query(CoincidenciaModel)
            .filter(
                (CoincidenciaModel.reporte_perdido_id == reporte_id)
                | (CoincidenciaModel.reporte_encontrado_id == reporte_id)
            )
            .all()
        )
        return [m.to_entity() for m in modelos]

    def listar_pendientes(self) -> list[Coincidencia]:
        """Obtiene todas las coincidencias con estado PENDIENTE.

        Returns:
            Lista de coincidencias pendientes de revisión.
        """
        modelos = (
            self._session.query(CoincidenciaModel)
            .filter_by(estado="PENDIENTE")
            .all()
        )
        return [m.to_entity() for m in modelos]

    def actualizar(self, coincidencia: Coincidencia) -> Coincidencia:
        """Actualiza una coincidencia existente en la base de datos.

        Args:
            coincidencia: Entidad Coincidencia con los datos actualizados.

        Returns:
            La coincidencia actualizada.
        """
        modelo = CoincidenciaModel.from_entity(coincidencia)
        self._session.merge(modelo)
        self._session.flush()
        return coincidencia

    def existe_coincidencia(self, perdido_id: str, encontrado_id: str) -> bool:
        """Verifica si ya existe una coincidencia entre dos reportes.

        Args:
            perdido_id: Identificador del reporte perdido.
            encontrado_id: Identificador del reporte encontrado.

        Returns:
            True si ya existe una coincidencia entre ambos reportes.
        """
        resultado = (
            self._session.query(CoincidenciaModel)
            .filter_by(
                reporte_perdido_id=perdido_id,
                reporte_encontrado_id=encontrado_id,
            )
            .first()
        )
        return resultado is not None
