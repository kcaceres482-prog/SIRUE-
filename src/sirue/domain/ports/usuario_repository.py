"""Puerto (interfaz) del repositorio de usuarios."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from sirue.domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    """Interfaz abstracta para la persistencia de usuarios.

    Define las operaciones que cualquier implementación de
    repositorio de usuarios debe soportar.
    """

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario:
        """Persiste un usuario nuevo."""
        ...

    @abstractmethod
    def obtener_por_id(self, id: str) -> Optional[Usuario]:
        """Obtiene un usuario por su ID."""
        ...

    @abstractmethod
    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por su correo electrónico."""
        ...

    @abstractmethod
    def listar_todos(self) -> list[Usuario]:
        """Lista todos los usuarios registrados."""
        ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario:
        """Actualiza la información de un usuario existente."""
        ...

    @abstractmethod
    def eliminar(self, id: str) -> bool:
        """Elimina un usuario y gestiona sus dependencias asociadas.

        Returns:
            True si el usuario existía y fue eliminado, False en caso contrario.
        """
        ...
