"""Puerto (interfaz) del repositorio de coincidencias."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from sirue.domain.entities.coincidencia import Coincidencia


class CoincidenciaRepository(ABC):
    """Interfaz abstracta para la persistencia de coincidencias.

    Define las operaciones que cualquier implementación de
    repositorio de coincidencias debe soportar.
    """

    @abstractmethod
    def guardar(self, coincidencia: Coincidencia) -> Coincidencia:
        """Persiste una coincidencia.

        Args:
            coincidencia: Coincidencia a guardar.

        Returns:
            La coincidencia guardada.
        """
        ...

    @abstractmethod
    def obtener_por_id(self, id: str) -> Optional[Coincidencia]:
        """Obtiene una coincidencia por su ID.

        Args:
            id: UUID de la coincidencia.

        Returns:
            La coincidencia si existe, None en caso contrario.
        """
        ...

    @abstractmethod
    def listar_por_reporte(self, reporte_id: str) -> list[Coincidencia]:
        """Lista todas las coincidencias asociadas a un reporte.

        Args:
            reporte_id: UUID del reporte (perdido o encontrado).

        Returns:
            Lista de coincidencias del reporte.
        """
        ...

    @abstractmethod
    def listar_pendientes(self) -> list[Coincidencia]:
        """Lista todas las coincidencias pendientes de revisión.

        Returns:
            Lista de coincidencias con estado PENDIENTE.
        """
        ...

    @abstractmethod
    def actualizar(self, coincidencia: Coincidencia) -> Coincidencia:
        """Actualiza una coincidencia existente.

        Args:
            coincidencia: Coincidencia con los datos actualizados.

        Returns:
            La coincidencia actualizada.
        """
        ...

    @abstractmethod
    def existe_coincidencia(self, perdido_id: str, encontrado_id: str) -> bool:
        """Verifica si ya existe una coincidencia entre dos reportes.

        Args:
            perdido_id: UUID del reporte perdido.
            encontrado_id: UUID del reporte encontrado.

        Returns:
            True si ya existe una coincidencia registrada.
        """
        ...
