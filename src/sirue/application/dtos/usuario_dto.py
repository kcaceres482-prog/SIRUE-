"""DTOs para autenticación, roles y gestión de usuarios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LoginInputDTO:
    """Datos de entrada para autenticación."""
    email: str
    password: str


@dataclass
class RegistroUsuarioInputDTO:
    """Datos de entrada para registro de nuevo usuario."""
    nombre: str
    email: str
    password: str
    confirm_password: Optional[str] = None
    telefono: Optional[str] = None
    rol: str = "usuario"


@dataclass
class UsuarioOutputDTO:
    """Datos de salida seguros de un usuario (sin hash)."""
    id: str
    nombre: str
    email: str
    telefono: Optional[str]
    rol: str
    fecha_registro: str
    es_admin: bool = False
    activo: bool = True
