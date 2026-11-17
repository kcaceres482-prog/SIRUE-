"""Value Object y validación centralizada de correo institucional para SIRUE (UAB)."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Optional

from sirue.domain.exceptions.domain_exceptions import ValidacionError

# Dominio institucional único y configurable para la Universidad Adventista de Bolivia
DOMINIO_INSTITUCIONAL: str = os.environ.get("SIRUE_INSTITUTIONAL_DOMAIN", "uab.edu.bo").strip().lower()

# Expresión regular para la parte local (nombre de usuario) del correo institucional
_LOCAL_PART_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+$")


def normalizar_email(email: Optional[str]) -> str:
    """Normaliza un correo electrónico eliminando espacios y convirtiéndolo a minúsculas.

    Args:
        email: Dirección de correo sin normalizar.

    Returns:
        Correo normalizado en minúsculas y sin espacios.
    """
    if email is None:
        return ""
    return email.strip().lower()


def validar_formato_email_institucional(email: Optional[str]) -> str:
    """Valida y normaliza un correo institucional para la Universidad Adventista de Bolivia.

    Acepta exclusivamente correos con el formato: nombre_usuario@uab.edu.bo

    Args:
        email: Cadena con el correo a validar.

    Returns:
        Correo normalizado (en minúsculas y sin espacios laterales).

    Raises:
        ValidacionError: Si el correo está vacío, mal formado o no pertenece al dominio @uab.edu.bo.
    """
    if email is None or not isinstance(email, str) or not email.strip():
        raise ValidacionError("El correo institucional es obligatorio.")

    email_limpio = normalizar_email(email)

    if "@" not in email_limpio:
        raise ValidacionError(
            f"El correo no tiene un formato válido. Debe pertenecer al dominio institucional @{DOMINIO_INSTITUCIONAL}."
        )

    partes = email_limpio.split("@")
    if len(partes) != 2:
        raise ValidacionError("El formato del correo es inválido (múltiples símbolos '@').")

    nombre_usuario, dominio = partes

    if not nombre_usuario:
        raise ValidacionError("El nombre de usuario del correo institucional no puede estar vacío.")

    if not _LOCAL_PART_REGEX.match(nombre_usuario):
        raise ValidacionError(
            f"El nombre de usuario '{nombre_usuario}' contiene caracteres no permitidos."
        )

    if dominio != DOMINIO_INSTITUCIONAL:
        raise ValidacionError(
            f"Dominio no autorizado: '@{dominio}'. Solo se permiten correos institucionales con dominio @{DOMINIO_INSTITUCIONAL}."
        )

    return email_limpio


def es_email_institucional_valido(email: Optional[str]) -> bool:
    """Verifica si un correo cumple con el formato institucional UAB sin lanzar excepciones.

    Útil para validación inmediata y reactiva en interfaces de usuario (Frontend).

    Args:
        email: Correo a evaluar.

    Returns:
        True si es válido y pertenece a @uab.edu.bo, False de lo contrario.
    """
    try:
        validar_formato_email_institucional(email)
        return True
    except ValidacionError:
        return False


@dataclass(frozen=True)
class EmailInstitucional:
    """Value Object inmutable que encapsula un correo institucional validado."""

    valor: str

    def __init__(self, valor: str) -> None:
        email_valido = validar_formato_email_institucional(valor)
        object.__setattr__(self, "valor", email_valido)

    def __str__(self) -> str:
        return self.valor

    def __repr__(self) -> str:
        return f"EmailInstitucional('{self.valor}')"
