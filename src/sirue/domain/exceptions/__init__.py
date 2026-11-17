"""Módulo de excepciones del dominio."""

from sirue.domain.exceptions.domain_exceptions import (
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

__all__ = [
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
]
