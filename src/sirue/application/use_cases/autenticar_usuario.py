"""Caso de uso: Autenticar usuario con credenciales institucionales y verificación de roles."""

from __future__ import annotations

from sirue.application.dtos.usuario_dto import LoginInputDTO, UsuarioOutputDTO
from sirue.application.services.password_hasher import PasswordHasher
from sirue.domain.exceptions.domain_exceptions import (
    CredencialesInvalidasError,
    CuentaBloqueadaError,
    ValidacionError,
)
from sirue.domain.ports.usuario_repository import UsuarioRepository
from sirue.domain.value_objects.email_institucional import (
    validar_formato_email_institucional,
)


class AutenticarUsuario:
    """Caso de uso para el inicio de sesión y validación de permisos de acceso."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def ejecutar(self, dto: LoginInputDTO) -> UsuarioOutputDTO:
        """Verifica las credenciales institucionales y retorna la información segura del usuario.

        Args:
            dto: Credenciales provistas (email y contraseña).

        Returns:
            UsuarioOutputDTO con los datos del usuario autenticado.

        Raises:
            ValidacionError: Si los campos están vacíos o el correo no pertenece al dominio institucional @uab.edu.bo.
            CredencialesInvalidasError: Si el usuario no existe o la contraseña es incorrecta.
        """
        raw_email = (dto.email or "").strip()
        password = dto.password or ""

        if not raw_email or not password:
            raise ValidacionError("Debes ingresar el correo institucional y la contraseña.")

        # Validación estricta del dominio institucional
        email = validar_formato_email_institucional(raw_email)

        usuario = self._usuario_repo.obtener_por_email(email)
        if not usuario or not usuario.password_hash:
            raise CredencialesInvalidasError("Credenciales incorrectas. Verifica tu correo y contraseña.")

        if not PasswordHasher.verificar_password(password, usuario.password_hash):
            raise CredencialesInvalidasError("Credenciales incorrectas. Verifica tu correo y contraseña.")

        if not usuario.esta_activo():
            raise CuentaBloqueadaError(
                "Tu cuenta ha sido bloqueada temporalmente. Comunícate con el administrador del sistema."
            )

        return UsuarioOutputDTO(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            telefono=usuario.telefono,
            rol=usuario.rol.value,
            fecha_registro=usuario.fecha_registro.isoformat(),
            es_admin=usuario.es_admin(),
            activo=usuario.esta_activo(),
        )
