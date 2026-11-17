"""Modelo SQLAlchemy para la entidad ReporteObjeto."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus
from sirue.infrastructure.persistence.database import Base


class ReporteModel(Base):
    """Representación en base de datos de un reporte de objeto perdido/encontrado."""

    __tablename__ = "reportes"

    id: str = Column(String, primary_key=True)
    tipo: str = Column(String, nullable=False)
    titulo: str = Column(String, nullable=False)
    descripcion: str = Column(Text, nullable=False)
    categoria: str = Column(String, nullable=False)
    latitud: float | None = Column(Float, nullable=True, default=None)
    longitud: float | None = Column(Float, nullable=True, default=None)
    referencia_interna: str = Column(String, nullable=False)
    fecha_hora_incidente: datetime = Column(DateTime, nullable=False)
    usuario_id: str = Column(String, ForeignKey("usuarios.id"), nullable=False)
    foto_ruta: str | None = Column(String, nullable=True)
    palabras_clave: str | None = Column(Text, nullable=True)
    estado: str = Column(String, nullable=False, default="ACTIVO")
    fecha_creacion: datetime = Column(DateTime, nullable=False)

    def to_entity(self) -> ReporteObjeto:
        """Convierte el modelo de base de datos a entidad de dominio.

        Reconstruye los Value Objects (UbicacionCampus, FechaHoraIncidente,
        CategoriaObjeto) a partir de las columnas almacenadas.

        Returns:
            Instancia de ReporteObjeto.
        """
        ubicacion = UbicacionCampus(
            referencia_interna=self.referencia_interna,
        )

        dt_incidente = self.fecha_hora_incidente
        if dt_incidente and dt_incidente.tzinfo is None:
            dt_incidente = dt_incidente.replace(tzinfo=timezone.utc)
        fecha_hora = FechaHoraIncidente(valor=dt_incidente)

        categoria = CategoriaObjeto(self.categoria)

        palabras: list[str] = []
        if self.palabras_clave:
            palabras = json.loads(self.palabras_clave)

        dt_creacion = self.fecha_creacion
        if dt_creacion and dt_creacion.tzinfo is None:
            dt_creacion = dt_creacion.replace(tzinfo=timezone.utc)

        return ReporteObjeto(
            id=self.id,
            tipo=TipoReporte(self.tipo),
            titulo=self.titulo,
            descripcion=self.descripcion,
            categoria=categoria,
            ubicacion=ubicacion,
            fecha_hora_incidente=fecha_hora,
            usuario_id=self.usuario_id,
            foto_ruta=self.foto_ruta,
            palabras_clave=palabras,
            estado=EstadoReporte(self.estado),
            fecha_creacion=dt_creacion,
        )

    @staticmethod
    def from_entity(reporte: ReporteObjeto) -> ReporteModel:
        """Crea un modelo de base de datos a partir de una entidad de dominio.

        Args:
            reporte: Entidad ReporteObjeto del dominio.

        Returns:
            Instancia de ReporteModel.
        """
        return ReporteModel(
            id=reporte.id,
            tipo=reporte.tipo.value,
            titulo=reporte.titulo,
            descripcion=reporte.descripcion,
            categoria=reporte.categoria.value,
            referencia_interna=reporte.ubicacion.referencia_interna,
            fecha_hora_incidente=reporte.fecha_hora_incidente.valor,
            usuario_id=reporte.usuario_id,
            foto_ruta=reporte.foto_ruta,
            palabras_clave=(
                json.dumps(reporte.palabras_clave)
                if reporte.palabras_clave
                else None
            ),
            estado=reporte.estado.value,
            fecha_creacion=reporte.fecha_creacion,
        )
