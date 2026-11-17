"""Capa de Aplicación del Sistema Digital de Objetos Perdidos y Encontrados (SIRUE)."""

from sirue.application.dtos import (
    CoincidenciaOutputDTO,
    EventoHistorialDTO,
    HistorialReporteDTO,
    LoginInputDTO,
    RegistroUsuarioInputDTO,
    ReporteInputDTO,
    ReporteOutputDTO,
    UsuarioOutputDTO,
)
from sirue.application.factories import ReporteFactory
from sirue.application.services import MotorCoincidencias, PasswordHasher
from sirue.application.use_cases import (
    AutenticarUsuario,
    GestionarReporteAdmin,
    ProcesarCoincidenciasYNotificar,
    RegistrarObjetoEncontrado,
    RegistrarObjetoPerdido,
    RegistrarUsuario,
)

__all__ = [
    # DTOs
    "ReporteInputDTO",
    "ReporteOutputDTO",
    "CoincidenciaOutputDTO",
    "LoginInputDTO",
    "RegistroUsuarioInputDTO",
    "UsuarioOutputDTO",
    "EventoHistorialDTO",
    "HistorialReporteDTO",
    # Factories
    "ReporteFactory",
    # Services
    "MotorCoincidencias",
    "PasswordHasher",
    # Use Cases
    "RegistrarObjetoPerdido",
    "RegistrarObjetoEncontrado",
    "ProcesarCoincidenciasYNotificar",
    "AutenticarUsuario",
    "RegistrarUsuario",
    "GestionarReporteAdmin",
]
