"""DTOs para el seguimiento y gestión de historial de reportes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sirue.application.dtos.reporte_dto import (
    CoincidenciaOutputDTO,
    ReporteOutputDTO,
)


@dataclass
class EventoHistorialDTO:
    """Evento cronológico en el ciclo de vida de un reporte."""
    fecha: str
    titulo: str
    descripcion: str
    tipo_evento: str  # 'CREACION', 'COINCIDENCIA', 'CAMBIO_ESTADO', 'NOTIFICACION'


@dataclass
class HistorialReporteDTO:
    """Historial enriquecido de un reporte de pertenencia."""
    reporte: ReporteOutputDTO
    estado_actual: str
    fue_encontrado: bool
    coincidencias: list[CoincidenciaOutputDTO] = field(default_factory=list)
    notificaciones: list[dict[str, Any]] = field(default_factory=list)
    eventos: list[EventoHistorialDTO] = field(default_factory=list)
