"""Módulo de gestión de sesión y protección centralizada de rutas para NiceGUI."""

from __future__ import annotations

import functools
from typing import Any, Callable, Optional

from nicegui import app, ui

from sirue.application.dtos.usuario_dto import UsuarioOutputDTO
from sirue.domain.entities.usuario import Usuario
from sirue.infrastructure.container import Container


def esta_autenticado() -> bool:
    """Indica si el cliente actual cuenta con una sesión autenticada válida."""
    try:
        return bool(app.storage.user.get("autenticado")) and bool(
            app.storage.user.get("usuario_id")
        )
    except Exception:
        return False


def obtener_usuario_actual(container: Container) -> Optional[Usuario]:
    """Obtiene la entidad Usuario de la base de datos correspondiente a la sesión activa.

    Si no hay sesión autenticada o el usuario ya no existe en la base de datos,
    limpia la cookie de sesión y retorna None.

    Args:
        container: Contenedor de dependencias de la aplicación.

    Returns:
        Instancia de Usuario autenticado o None.
    """
    try:
        if not app.storage.user.get("autenticado"):
            return None
        usuario_id = app.storage.user.get("usuario_id")
        if not usuario_id:
            return None
    except Exception:
        return None

    with container.database.get_session() as session:
        u_repo = container.usuario_repository(session)
        usuario = u_repo.obtener_por_id(str(usuario_id))
        if not usuario or not usuario.esta_activo():
            try:
                app.storage.user.clear()
            except Exception:
                pass
            return None

        # Sincronizar claims en la cookie de sesión
        try:
            app.storage.user["usuario_nombre"] = usuario.nombre
            app.storage.user["usuario_email"] = usuario.email
            app.storage.user["usuario_rol"] = usuario.rol.value
            app.storage.user["es_admin"] = usuario.es_admin()
        except Exception:
            pass

        return usuario


def iniciar_sesion(usuario: UsuarioOutputDTO) -> None:
    """Registra la identidad del usuario en la sesión cifrada del navegador.

    Args:
        usuario: DTO seguro del usuario autenticado.
    """
    app.storage.user["usuario_id"] = usuario.id
    app.storage.user["usuario_nombre"] = usuario.nombre
    app.storage.user["usuario_email"] = usuario.email
    app.storage.user["usuario_rol"] = usuario.rol
    app.storage.user["es_admin"] = usuario.es_admin
    app.storage.user["autenticado"] = True


def cerrar_sesion() -> None:
    """Destruye la sesión autenticada actual y redirige a la pantalla de login."""
    try:
        app.storage.user.clear()
    except Exception:
        pass
    ui.notify("Sesión cerrada correctamente.", type="info")
    ui.navigate.to("/login")


def ruta_protegida(
    container: Container,
    solo_admin: bool = False,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorador centralizado para proteger páginas y rutas en NiceGUI.

    - Si el usuario no está autenticado, detiene el renderizado y redirige a /login.
    - Si la ruta requiere privilegios de administrador y el usuario es normal,
      emite una notificación de advertencia y redirige a /.

    Args:
        container: Contenedor de dependencias del sistema.
        solo_admin: Si es True, restringe el acceso exclusivamente a rol 'admin'.
    """
    def decorador(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            usuario = obtener_usuario_actual(container)
            if not usuario:
                ui.navigate.to("/login")
                return None

            if solo_admin and not usuario.es_admin():
                ui.notify(
                    "Acceso denegado: Esta sección requiere privilegios administrativos.",
                    type="warning",
                    position="top",
                )
                ui.navigate.to("/")
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorador
