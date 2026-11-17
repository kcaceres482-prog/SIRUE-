"""Modelo SQLAlchemy para la entidad Usuario."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String

from sirue.domain.entities.usuario import RolUsuario, Usuario
from sirue.infrastructure.persistence.database import Base


class UsuarioModel(Base):
    """Representación en base de datos de un usuario del sistema."""

    __tablename__ = "usuarios"

    id: str = Column(String, primary_key=True)
    nombre: str = Column(String, nullable=False)
    email: str = Column(String, unique=True, nullable=False)
    telefono: str | None = Column(String, default="", nullable=True)
    fecha_registro: datetime = Column(DateTime, nullable=False)
    rol: str = Column(String, default="usuario", nullable=False)
    password_hash: str | None = Column(String, nullable=True)
    activo: bool = Column(Boolean, default=True, nullable=False)

    def to_entity(self) -> Usuario:
        """Convierte el modelo de base de datos a entidad de dominio.

        Returns:
            Instancia de Usuario.
        """
        dt_reg = self.fecha_registro
        if dt_reg and dt_reg.tzinfo is None:
            dt_reg = dt_reg.replace(tzinfo=timezone.utc)

        rol_str = getattr(self, "rol", "usuario") or "usuario"
        try:
            rol_enum = RolUsuario(rol_str)
        except ValueError:
            rol_enum = RolUsuario.USUARIO

        activo_val = getattr(self, "activo", True)
        if activo_val is None:
            activo_val = True

        return Usuario(
            id=self.id,
            nombre=self.nombre,
            email=self.email,
            telefono=self.telefono or "",
            fecha_registro=dt_reg,
            rol=rol_enum,
            password_hash=getattr(self, "password_hash", None),
            activo=bool(activo_val),
        )

    @staticmethod
    def from_entity(usuario: Usuario) -> UsuarioModel:
        """Crea un modelo de base de datos a partir de una entidad de dominio.

        Args:
            usuario: Entidad Usuario del dominio.

        Returns:
            Instancia de UsuarioModel.
        """
        rol_valor = usuario.rol.value if isinstance(usuario.rol, RolUsuario) else str(usuario.rol)
        return UsuarioModel(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            telefono=usuario.telefono,
            fecha_registro=usuario.fecha_registro,
            rol=rol_valor,
            password_hash=usuario.password_hash,
            activo=usuario.activo,
        )
