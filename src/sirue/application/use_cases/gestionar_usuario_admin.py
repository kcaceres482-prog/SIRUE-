"""Casos de uso para la administración y gestión completa de usuarios en SIRUE."""

from __future__ import annotations

from typing import Optional

from sirue.application.dtos.usuario_dto import UsuarioOutputDTO
from sirue.application.services.password_hasher import PasswordHasher
from sirue.domain.entities.usuario import RolUsuario, Usuario
from sirue.domain.exceptions.domain_exceptions import (
    AccesoDenegadoError,
    OperacionNoPermitidaError,
    UsuarioNoEncontradoError,
    ValidacionError,
)
from sirue.domain.ports.usuario_repository import UsuarioRepository


def _mapear_a_dto(usuario: Usuario) -> UsuarioOutputDTO:
    """Convierte una entidad Usuario en UsuarioOutputDTO."""
    return UsuarioOutputDTO(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        telefono=usuario.telefono,
        rol=usuario.rol.value if isinstance(usuario.rol, RolUsuario) else str(usuario.rol),
        fecha_registro=usuario.fecha_registro.isoformat() if usuario.fecha_registro else "",
        es_admin=usuario.es_admin(),
        activo=usuario.esta_activo(),
    )


class RestablecerContrasenaUsuarioUseCase:
    """Caso de uso para restablecer la contraseña de un usuario."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def ejecutar(
        self,
        usuario_id: str,
        nueva_contrasena: str,
        admin_id: Optional[str] = None,
    ) -> UsuarioOutputDTO:
        """Restablece la contraseña de un usuario.

        Args:
            usuario_id: ID del usuario a modificar.
            nueva_contrasena: Nueva contraseña en texto plano (mínimo 6 caracteres).
            admin_id: ID del administrador que realiza la acción (opcional).

        Returns:
            UsuarioOutputDTO actualizado.

        Raises:
            AccesoDenegadoError: Si admin_id no es un administrador.
            UsuarioNoEncontradoError: Si el usuario objetivo no existe.
            ValidacionError: Si la contraseña no cumple con los requisitos mínimos.
        """
        if admin_id:
            admin = self._usuario_repo.obtener_por_id(admin_id)
            if not admin or not admin.es_admin():
                raise AccesoDenegadoError("Solo un administrador puede restablecer contraseñas de usuarios.")

        if not nueva_contrasena or len(nueva_contrasena.strip()) < 6:
            raise ValidacionError("La nueva contraseña debe tener al menos 6 caracteres.")

        usuario = self._usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"No se encontró el usuario con ID {usuario_id}.")

        p_hash = PasswordHasher.hashear_password(nueva_contrasena.strip())
        usuario.cambiar_password_hash(p_hash)
        actualizado = self._usuario_repo.actualizar(usuario)
        return _mapear_a_dto(actualizado)


class CambiarRolUsuarioUseCase:
    """Caso de uso para ascender o cambiar el rol de un usuario."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def ejecutar(
        self,
        admin_id: str,
        usuario_id: str,
        nuevo_rol: str | RolUsuario,
    ) -> UsuarioOutputDTO:
        """Cambia el rol de un usuario con salvaguarda de autoprotección.

        Args:
            admin_id: ID del administrador que ejecuta el cambio.
            usuario_id: ID del usuario afectado.
            nuevo_rol: Nuevo rol a asignar ('admin' o 'usuario').

        Returns:
            UsuarioOutputDTO actualizado.

        Raises:
            AccesoDenegadoError: Si quien ejecuta no es administrador.
            OperacionNoPermitidaError: Si el administrador intenta degradarse a sí mismo.
            UsuarioNoEncontradoError: Si el usuario objetivo no existe.
        """
        admin = self._usuario_repo.obtener_por_id(admin_id)
        if not admin or not admin.es_admin():
            raise AccesoDenegadoError("Solo un administrador puede modificar roles de usuario.")

        rol_destino = RolUsuario.ADMIN if str(nuevo_rol).lower() == "admin" else RolUsuario.USUARIO

        # Autoprotección: no permitir que el admin se quite sus propios permisos
        if admin_id == usuario_id and rol_destino != RolUsuario.ADMIN:
            raise OperacionNoPermitidaError("No puedes degradar tu propia cuenta de administrador.")

        usuario = self._usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"No se encontró el usuario con ID {usuario_id}.")

        usuario.cambiar_rol(rol_destino)
        actualizado = self._usuario_repo.actualizar(usuario)
        return _mapear_a_dto(actualizado)


class CambiarEstadoUsuarioUseCase:
    """Caso de uso para suspender (bloquear) o reactivar la cuenta de un usuario."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def ejecutar(
        self,
        admin_id: str,
        usuario_id: str,
        activo: bool,
    ) -> UsuarioOutputDTO:
        """Suspende o activa una cuenta de usuario con salvaguarda de autoprotección.

        Args:
            admin_id: ID del administrador que ejecuta la acción.
            usuario_id: ID del usuario afectado.
            activo: True para habilitar, False para bloquear.

        Returns:
            UsuarioOutputDTO actualizado.

        Raises:
            AccesoDenegadoError: Si quien ejecuta no es administrador.
            OperacionNoPermitidaError: Si el administrador intenta bloquearse a sí mismo.
            UsuarioNoEncontradoError: Si el usuario objetivo no existe.
        """
        admin = self._usuario_repo.obtener_por_id(admin_id)
        if not admin or not admin.es_admin():
            raise AccesoDenegadoError("Solo un administrador puede cambiar el estado de las cuentas.")

        # Autoprotección: no permitir que el admin se bloquee a sí mismo
        if admin_id == usuario_id and not activo:
            raise OperacionNoPermitidaError("No puedes bloquear tu propia cuenta de administrador.")

        usuario = self._usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"No se encontró el usuario con ID {usuario_id}.")

        if activo:
            usuario.activar()
        else:
            usuario.bloquear()

        actualizado = self._usuario_repo.actualizar(usuario)
        return _mapear_a_dto(actualizado)


class EliminarUsuarioUseCase:
    """Caso de uso para eliminar permanentemente un usuario del sistema."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def ejecutar(self, admin_id: str, usuario_id: str) -> bool:
        """Elimina la cuenta de un usuario con salvaguarda de autoprotección.

        Args:
            admin_id: ID del administrador que ejecuta la eliminación.
            usuario_id: ID del usuario a eliminar.

        Returns:
            True si fue eliminado exitosamente.

        Raises:
            AccesoDenegadoError: Si quien ejecuta no es administrador.
            OperacionNoPermitidaError: Si el administrador intenta eliminarse a sí mismo.
            UsuarioNoEncontradoError: Si el usuario objetivo no existe.
        """
        admin = self._usuario_repo.obtener_por_id(admin_id)
        if not admin or not admin.es_admin():
            raise AccesoDenegadoError("Solo un administrador puede eliminar usuarios.")

        # Autoprotección: no permitir que el admin se elimine a sí mismo
        if admin_id == usuario_id:
            raise OperacionNoPermitidaError("No puedes eliminar tu propia cuenta de administrador.")

        usuario = self._usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"No se encontró el usuario con ID {usuario_id}.")

        return self._usuario_repo.eliminar(usuario_id)


class ListarUsuariosAdminUseCase:
    """Caso de uso para obtener la lista de todos los usuarios registrados."""

    def __init__(self, usuario_repo: UsuarioRepository) -> None:
        self._usuario_repo = usuario_repo

    def ejecutar(self, admin_id: str) -> list[UsuarioOutputDTO]:
        """Lista todos los usuarios del sistema para el panel administrativo.

        Args:
            admin_id: ID del administrador solicitante.

        Returns:
            Lista de UsuarioOutputDTO.

        Raises:
            AccesoDenegadoError: Si quien solicita no es administrador.
        """
        admin = self._usuario_repo.obtener_por_id(admin_id)
        if not admin or not admin.es_admin():
            raise AccesoDenegadoError("Acceso denegado: se requieren permisos de administrador.")

        usuarios = self._usuario_repo.listar_todos()
        return [_mapear_a_dto(u) for u in usuarios]
