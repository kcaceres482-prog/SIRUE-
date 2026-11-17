"""Configuración y registro de rutas de NiceGUI con protección de acceso para SIRUE."""

from __future__ import annotations

from pathlib import Path

from nicegui import app, ui

from sirue.infrastructure.container import Container
from sirue.presentation.auth_session import (
    cerrar_sesion,
    obtener_usuario_actual,
    ruta_protegida,
)
from sirue.presentation.pages.admin import crear_pagina_admin
from sirue.presentation.pages.coincidencias import crear_pagina_coincidencias
from sirue.presentation.pages.home import crear_pagina_home
from sirue.presentation.pages.login import crear_pagina_login
from sirue.presentation.pages.mis_reportes import crear_pagina_mis_reportes
from sirue.presentation.pages.registrar_encontrado import (
    crear_pagina_registrar_encontrado,
)
from sirue.presentation.pages.registrar_perdido import (
    crear_pagina_registrar_perdido,
)


def crear_app(container: Container) -> None:
    """Configura las rutas, archivos estáticos y páginas protegidas de la interfaz NiceGUI.

    Aplica el flujo de autenticación y autorización por roles:
    - Usuario no autenticado en ruta raíz (/) o protegida -> Redirige al Login.
    - Usuario administrador -> Acceso al panel administrativo (/admin).
    - Usuario estándar -> Acceso a la zona de reportes (/).

    Args:
        container: Contenedor de dependencias de la aplicación.
    """
    # 1. Asegurar directorios de archivos estáticos y uploads
    base_dir = Path(__file__).parent
    static_dir = base_dir / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # 2. Servir archivos estáticos y fotos subidas
    app.add_static_files("/static", str(static_dir))
    app.add_static_files("/uploads", str(uploads_dir))

    # 3. Ruta Raíz con discriminación de autenticación y roles
    @ui.page("/", title="SIRUE — Universidad Adventista de Bolivia")
    def pagina_home() -> None:
        usuario = obtener_usuario_actual(container)
        if not usuario:
            # Flujo 1: Usuario no autenticado -> Se muestra la pantalla de Login
            ui.navigate.to("/login")
            return

        if usuario.es_admin():
            # Flujo 2: Administrador -> Debe acceder al panel administrativo
            ui.navigate.to("/admin")
            return

        # Flujo 3: Usuario normal -> Acceso a la zona de reportes
        crear_pagina_home(container)

    # 4. Ruta Pública de Autenticación y Registro Institucional
    @ui.page("/login", title="Acceso Institucional — SIRUE UAB")
    def pagina_login() -> None:
        usuario = obtener_usuario_actual(container)
        if usuario:
            # Si el usuario ya está autenticado, redirigir según su rol
            if usuario.es_admin():
                ui.navigate.to("/admin")
            else:
                ui.navigate.to("/")
            return

        crear_pagina_login(container)

    # 5. Cierre de Sesión
    @ui.page("/logout")
    def pagina_logout() -> None:
        cerrar_sesion()

    # 6. Rutas Protegidas (Requieren inicio de sesión institucional)
    @ui.page("/reportar-perdido", title="Reportar Objeto Perdido — SIRUE UAB")
    @ruta_protegida(container)
    def pagina_reportar_perdido() -> None:
        crear_pagina_registrar_perdido(container)

    @ui.page("/reportar-encontrado", title="Registrar Hallazgo — SIRUE UAB")
    @ruta_protegida(container)
    def pagina_reportar_encontrado() -> None:
        crear_pagina_registrar_encontrado(container)

    @ui.page("/mis-reportes", title="Mis Reportes — SIRUE UAB")
    @ruta_protegida(container)
    def pagina_mis_reportes() -> None:
        crear_pagina_mis_reportes(container)

    @ui.page("/coincidencias", title="Centro de Coincidencias — SIRUE UAB")
    @ruta_protegida(container)
    def pagina_coincidencias() -> None:
        crear_pagina_coincidencias(container)

    # 7. Ruta Administrativa (Requiere autenticación Y rol de administrador)
    @ui.page("/admin", title="Panel Administrativo — SIRUE UAB")
    @ruta_protegida(container, solo_admin=True)
    def pagina_admin() -> None:
        crear_pagina_admin(container)
