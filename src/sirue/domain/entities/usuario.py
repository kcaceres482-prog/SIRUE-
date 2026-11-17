"""Entidad que representa un usuario del sistema SIRUE con soporte de roles y credenciales."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Optional

from sirue.domain.exceptions.domain_exceptions import ValidacionError
from sirue.domain.value_objects.email_institucional import (
    DOMINIO_INSTITUCIONAL,
    validar_formato_email_institucional,
)


class RolUsuario(Enum):
    """Roles de acceso y privilegios dentro del sistema SIRUE."""
    ADMIN = "admin"
    USUARIO = "usuario"


class Usuario:
    """Usuario registrado en el sistema de objetos perdidos y encontrados.

    Attributes:
        id: Identificador único (UUID).
        nombre: Nombre completo del usuario.
        email: Correo electrónico institucional (@uab.edu.bo).
        telefono: Número de teléfono (opcional).
        fecha_registro: Fecha y hora de registro en el sistema.
        rol: Rol del usuario ('admin' o 'usuario').
        password_hash: Hash de la contraseña del usuario.
        activo: Estado de la cuenta (True si está activa, False si está suspendida/bloqueada).
    """

    DOMINIO_PERMITIDO: str = DOMINIO_INSTITUCIONAL
    _EMAIL_REGEX = re.compile(rf"^[a-zA-Z0-9._%+\-]+@{re.escape(DOMINIO_INSTITUCIONAL)}$")

    def __init__(
        self,
        id: str,
        nombre: str,
        email: str,
        telefono: Optional[str] = None,
        fecha_registro: Optional[datetime] = None,
        rol: RolUsuario = RolUsuario.USUARIO,
        password_hash: Optional[str] = None,
        activo: bool = True,
    ) -> None:
        """Inicializa un usuario con validación de datos e identidad institucional.

        Args:
            id: UUID del usuario.
            nombre: Nombre completo (no vacío).
            email: Correo electrónico institucional @uab.edu.bo.
            telefono: Número de teléfono opcional.
            fecha_registro: Fecha de registro; si es None, se usa la fecha actual.
            rol: Rol de permisos en la plataforma (por defecto 'usuario').
            password_hash: Hash de la contraseña almacenada.
            activo: Estado de la cuenta (por defecto True).

        Raises:
            ValidacionError: Si el nombre está vacío o el email no es institucional válido.
        """
        if not nombre or not nombre.strip():
            raise ValidacionError("El nombre del usuario no puede estar vacío.")

        self.email = validar_formato_email_institucional(email)
        self.id = id
        self.nombre = nombre.strip()
        self.telefono = (telefono or "").strip()
        self.fecha_registro = fecha_registro or datetime.now(timezone.utc)
        if isinstance(rol, RolUsuario):
            self.rol = rol
        else:
            try:
                self.rol = RolUsuario(str(rol).lower().strip())
            except ValueError:
                self.rol = RolUsuario.USUARIO
        self.password_hash = password_hash
        self.activo = bool(activo)

    def es_admin(self) -> bool:
        """Indica si el usuario tiene privilegios administrativos."""
        return self.rol == RolUsuario.ADMIN

    def es_usuario(self) -> bool:
        """Indica si el usuario tiene privilegios estándar."""
        return self.rol == RolUsuario.USUARIO

    def esta_activo(self) -> bool:
        """Indica si la cuenta del usuario se encuentra activa."""
        return bool(self.activo)

    def activar(self) -> None:
        """Reactiva la cuenta del usuario."""
        self.activo = True

    def bloquear(self) -> None:
        """Bloquea o suspende temporalmente la cuenta del usuario."""
        self.activo = False

    def cambiar_rol(self, nuevo_rol: RolUsuario | str) -> None:
        """Actualiza el rol del usuario."""
        if isinstance(nuevo_rol, RolUsuario):
            self.rol = nuevo_rol
        else:
            try:
                self.rol = RolUsuario(str(nuevo_rol).lower().strip())
            except ValueError:
                self.rol = RolUsuario.USUARIO

    def cambiar_password_hash(self, nuevo_hash: str) -> None:
        """Actualiza el hash de la contraseña del usuario."""
        self.password_hash = nuevo_hash

    def actualizar_telefono(self, nuevo_telefono: str) -> None:
        """Actualiza el número de contacto/WhatsApp del usuario."""
        self.telefono = (nuevo_telefono or "").strip()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Usuario):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"Usuario(id={self.id!r}, nombre={self.nombre!r}, email={self.email!r}, rol={self.rol.value})"
