"""Módulo de entidades del dominio."""

from sirue.domain.entities.coincidencia import Coincidencia, EstadoCoincidencia
from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.entities.usuario import RolUsuario, Usuario

__all__ = [
    "Usuario",
    "RolUsuario",
    "ReporteObjeto",
    "TipoReporte",
    "EstadoReporte",
    "Coincidencia",
    "EstadoCoincidencia",
]
