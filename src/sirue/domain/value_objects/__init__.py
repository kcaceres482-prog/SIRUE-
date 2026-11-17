"""Módulo de Value Objects del dominio."""

from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.email_institucional import (
    DOMINIO_INSTITUCIONAL,
    EmailInstitucional,
    es_email_institucional_valido,
    normalizar_email,
    validar_formato_email_institucional,
)
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus

__all__ = [
    "CategoriaObjeto",
    "DOMINIO_INSTITUCIONAL",
    "EmailInstitucional",
    "FechaHoraIncidente",
    "UbicacionCampus",
    "es_email_institucional_valido",
    "normalizar_email",
    "validar_formato_email_institucional",
]
