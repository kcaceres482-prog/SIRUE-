"""Entidad que representa una coincidencia entre un reporte perdido y uno encontrado."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sirue.domain.exceptions.domain_exceptions import ValidacionError


class EstadoCoincidencia(Enum):
    """Estado de la coincidencia detectada."""
    PENDIENTE = "PENDIENTE"
    CONFIRMADA = "CONFIRMADA"
    DESCARTADA = "DESCARTADA"


class Coincidencia:
    """Coincidencia detectada entre un reporte de objeto perdido y uno encontrado.

    Attributes:
        id: Identificador único (UUID).
        reporte_perdido_id: ID del reporte de objeto perdido.
        reporte_encontrado_id: ID del reporte de objeto encontrado.
        puntuacion: Puntuación de coincidencia entre 0.0 y 1.0.
        fecha_deteccion: Fecha y hora en que se detectó la coincidencia.
        estado: Estado actual de la coincidencia.
        detalles: Desglose de la puntuación por criterio.
    """

    def __init__(
        self,
        id: str,
        reporte_perdido_id: str,
        reporte_encontrado_id: str,
        puntuacion: float,
        fecha_deteccion: datetime | None = None,
        estado: EstadoCoincidencia = EstadoCoincidencia.PENDIENTE,
        detalles: dict | None = None,
    ) -> None:
        """Inicializa una coincidencia.

        Args:
            id: UUID de la coincidencia.
            reporte_perdido_id: UUID del reporte perdido.
            reporte_encontrado_id: UUID del reporte encontrado.
            puntuacion: Puntuación total [0.0, 1.0].
            fecha_deteccion: Fecha de detección; si es None se usa la actual.
            estado: Estado de la coincidencia.
            detalles: Diccionario con el desglose de la puntuación.

        Raises:
            ValidacionError: Si la puntuación está fuera de rango.
        """
        if not (0.0 <= puntuacion <= 1.0):
            raise ValidacionError(
                f"La puntuación debe estar entre 0.0 y 1.0. Valor: {puntuacion}"
            )

        self.id = id
        self.reporte_perdido_id = reporte_perdido_id
        self.reporte_encontrado_id = reporte_encontrado_id
        self.puntuacion = puntuacion
        self.fecha_deteccion = fecha_deteccion or datetime.now(timezone.utc)
        self.estado = (
            estado
            if isinstance(estado, EstadoCoincidencia)
            else EstadoCoincidencia(estado)
        )
        self.detalles = detalles or {}

    def confirmar(self) -> None:
        """Confirma la coincidencia entre los dos reportes."""
        self.estado = EstadoCoincidencia.CONFIRMADA

    def descartar(self) -> None:
        """Descarta la coincidencia como no válida."""
        self.estado = EstadoCoincidencia.DESCARTADA

    def es_relevante(self, umbral: float = 0.5) -> bool:
        """Indica si la coincidencia es relevante según un umbral de puntuación.

        Args:
            umbral: Puntuación mínima para considerar relevante (por defecto 0.5).

        Returns:
            True si la puntuación es mayor o igual al umbral.
        """
        return self.puntuacion >= umbral

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Coincidencia):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"Coincidencia(id={self.id!r}, puntuacion={self.puntuacion:.2f}, "
            f"estado={self.estado.value})"
        )
