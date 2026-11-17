"""Modelo SQLAlchemy para la entidad Coincidencia."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from sirue.domain.entities.coincidencia import (
    Coincidencia,
    EstadoCoincidencia,
)
from sirue.infrastructure.persistence.database import Base


class CoincidenciaModel(Base):
    """Representación en base de datos de una coincidencia entre reportes."""

    __tablename__ = "coincidencias"

    id: str = Column(String, primary_key=True)
    reporte_perdido_id: str = Column(
        String, ForeignKey("reportes.id"), nullable=False
    )
    reporte_encontrado_id: str = Column(
        String, ForeignKey("reportes.id"), nullable=False
    )
    puntuacion: float = Column(Float, nullable=False)
    fecha_deteccion: datetime = Column(DateTime, nullable=False)
    estado: str = Column(String, nullable=False, default="PENDIENTE")
    detalles: str | None = Column(Text, nullable=True)

    def to_entity(self) -> Coincidencia:
        """Convierte el modelo de base de datos a entidad de dominio.

        Returns:
            Instancia de Coincidencia.
        """
        detalles_dict: dict = {}
        if self.detalles:
            detalles_dict = json.loads(self.detalles)

        dt_det = self.fecha_deteccion
        if dt_det and dt_det.tzinfo is None:
            dt_det = dt_det.replace(tzinfo=timezone.utc)

        return Coincidencia(
            id=self.id,
            reporte_perdido_id=self.reporte_perdido_id,
            reporte_encontrado_id=self.reporte_encontrado_id,
            puntuacion=self.puntuacion,
            fecha_deteccion=dt_det,
            estado=EstadoCoincidencia(self.estado),
            detalles=detalles_dict,
        )

    @staticmethod
    def from_entity(coincidencia: Coincidencia) -> CoincidenciaModel:
        """Crea un modelo de base de datos a partir de una entidad de dominio.

        Args:
            coincidencia: Entidad Coincidencia del dominio.

        Returns:
            Instancia de CoincidenciaModel.
        """
        return CoincidenciaModel(
            id=coincidencia.id,
            reporte_perdido_id=coincidencia.reporte_perdido_id,
            reporte_encontrado_id=coincidencia.reporte_encontrado_id,
            puntuacion=coincidencia.puntuacion,
            fecha_deteccion=coincidencia.fecha_deteccion,
            estado=coincidencia.estado.value,
            detalles=(
                json.dumps(coincidencia.detalles)
                if coincidencia.detalles
                else None
            ),
        )
