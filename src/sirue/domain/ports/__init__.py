"""Módulo de puertos (interfaces abstractas) del dominio."""

from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.domain.ports.foto_storage import FotoStorage
from sirue.domain.ports.notificacion_service import NotificacionService
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.domain.ports.usuario_repository import UsuarioRepository

__all__ = [
    "UsuarioRepository",
    "ReporteRepository",
    "CoincidenciaRepository",
    "FotoStorage",
    "NotificacionService",
]
