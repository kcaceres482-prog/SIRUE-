"""Capa de Dominio del Sistema Digital de Objetos Perdidos y Encontrados (SIRUE)."""

from sirue.domain.entities import (
    Coincidencia,
    EstadoCoincidencia,
    EstadoReporte,
    ReporteObjeto,
    RolUsuario,
    TipoReporte,
    Usuario,
)
from sirue.domain.exceptions import (
    AccesoDenegadoError,
    CoincidenciaNoEncontradaError,
    CredencialesInvalidasError,
    DescripcionInsuficienteError,
    EmailYaRegistradoError,
    FotoRequeridaError,
    ReporteNoEncontradoError,
    SIRUEDomainError,
    UsuarioNoEncontradoError,
    ValidacionError,
)
from sirue.domain.ports import (
    CoincidenciaRepository,
    FotoStorage,
    NotificacionService,
    ReporteRepository,
    UsuarioRepository,
)
from sirue.domain.value_objects import (
    CategoriaObjeto,
    FechaHoraIncidente,
    UbicacionCampus,
)

__all__ = [
    # Entidades
    "Usuario",
    "RolUsuario",
    "ReporteObjeto",
    "TipoReporte",
    "EstadoReporte",
    "Coincidencia",
    "EstadoCoincidencia",
    # Value Objects
    "UbicacionCampus",
    "FechaHoraIncidente",
    "CategoriaObjeto",
    # Excepciones
    "SIRUEDomainError",
    "ValidacionError",
    "ReporteNoEncontradoError",
    "UsuarioNoEncontradoError",
    "CoincidenciaNoEncontradaError",
    "FotoRequeridaError",
    "DescripcionInsuficienteError",
    "CredencialesInvalidasError",
    "EmailYaRegistradoError",
    "AccesoDenegadoError",
    # Puertos
    "UsuarioRepository",
    "ReporteRepository",
    "CoincidenciaRepository",
    "FotoStorage",
    "NotificacionService",
]
