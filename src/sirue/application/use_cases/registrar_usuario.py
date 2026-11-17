"""Caso de uso: Registro de nuevos usuarios con validación institucional y contraseña segura."""

from __future__ import annotations

from datetime import datetime, timezone
import re
import uuid

from sirue.application.dtos.usuario_dto import (
    RegistroUsuarioInputDTO,
    UsuarioOutputDTO,
)
from sirue.application.services.password_hasher import PasswordHasher
from sirue.domain.entities.usuario import RolUsuario, Usuario
from sirue.domain.exceptions.domain_exceptions import (
    AccesoDenegadoError,
    EmailYaRegistradoError,
    ValidacionError,
)
from sirue.domain.ports.usuario_repository import UsuarioRepository
from sirue.domain.value_objects.email_institucional import (
    validar_formato_email_institucional,
)


class RegistrarUsuario:
    """Caso de uso para registrar nuevos estudiantes o administradores autorizados."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def ejecutar(
        self,
        dto: RegistroUsuarioInputDTO,
        es_registro_publico: bool = False,
    ) -> UsuarioOutputDTO:
        """Registra un nuevo usuario en la plataforma.

        Args:
            dto: Información requerida para el registro del usuario.
            es_registro_publico: Si es True, prohíbe la asignación de rol administrador
                                 y fuerza el rol estándar de usuario.

        Returns:
            UsuarioOutputDTO con los datos seguros del usuario registrado.

        Raises:
            ValidacionError: Si la contraseña es corta, las contraseñas no coinciden,
                             o el correo no cumple con el dominio institucional @uab.edu.bo.
            AccesoDenegadoError: Si se intenta crear un administrador desde el registro público.
            EmailYaRegistradoError: Si el correo ya existe en el sistema.
        """
        nombre = (dto.nombre or "").strip()
        if not nombre:
            raise ValidacionError("El nombre completo del usuario es obligatorio.")

        email = validar_formato_email_institucional(dto.email)
        password = dto.password or ""

        # Validación de coincidencia de contraseñas
        if dto.confirm_password is not None and password != dto.confirm_password:
            raise ValidacionError("Las contraseñas no coinciden.")

        if len(password) < 6:
            raise ValidacionError("La contraseña debe tener al menos 6 caracteres.")

        # Normalización y validación del número de teléfono / WhatsApp
        raw_tel = (dto.telefono or "").strip()
        if raw_tel:
            solo_digitos = re.sub(r"\D", "", raw_tel)
            if len(solo_digitos) < 8:
                raise ValidacionError("El número de celular/WhatsApp debe tener al menos 8 dígitos.")
            tel_limpio = re.sub(r"[^\d+]", "", raw_tel)
        else:
            tel_limpio = ""

        # Verificar unicidad del correo electrónico
        existente = self._usuario_repo.obtener_por_email(email)
        if existente:
            raise EmailYaRegistradoError(f"El correo institucional '{email}' ya se encuentra registrado.")

        # Restricción de privilegios en el registro público
        if es_registro_publico:
            if dto.rol and str(dto.rol).lower().strip() == "admin":
                raise AccesoDenegadoError(
                    "No está permitido asignarse privilegios administrativos mediante el registro público."
                )
            rol_enum = RolUsuario.USUARIO
        else:
            try:
                rol_enum = RolUsuario(str(dto.rol).lower().strip())
            except ValueError:
                rol_enum = RolUsuario.USUARIO

        # Hash criptográfico de la contraseña
        p_hash = PasswordHasher.hashear_password(password)

        nuevo_usuario = Usuario(
            id=str(uuid.uuid4()),
            nombre=nombre,
            email=email,
            telefono=tel_limpio,
            fecha_registro=datetime.now(timezone.utc),
            rol=rol_enum,
            password_hash=p_hash,
        )

        guardado = self._usuario_repo.guardar(nuevo_usuario)

        return UsuarioOutputDTO(
            id=guardado.id,
            nombre=guardado.nombre,
            email=guardado.email,
            telefono=guardado.telefono,
            rol=guardado.rol.value,
            fecha_registro=guardado.fecha_registro.isoformat(),
            es_admin=guardado.es_admin(),
            activo=guardado.esta_activo(),
        )
