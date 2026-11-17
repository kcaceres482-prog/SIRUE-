"""Módulo de DTOs de la aplicación."""

from sirue.application.dtos.historial_dto import (
    EventoHistorialDTO,
    HistorialReporteDTO,
)
from sirue.application.dtos.reporte_dto import (
    CoincidenciaOutputDTO,
    ReporteInputDTO,
    ReporteOutputDTO,
)
from sirue.application.dtos.usuario_dto import (
    LoginInputDTO,
    RegistroUsuarioInputDTO,
    UsuarioOutputDTO,
)

__all__ = [
    "ReporteInputDTO",
    "ReporteOutputDTO",
    "CoincidenciaOutputDTO",
    "LoginInputDTO",
    "RegistroUsuarioInputDTO",
    "UsuarioOutputDTO",
    "EventoHistorialDTO",
    "HistorialReporteDTO",
]
