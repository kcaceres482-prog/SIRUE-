"""Barra de navegación y cabecera global accesible y responsiva para SIRUE."""

from __future__ import annotations

from typing import Optional

from nicegui import ui

from sirue.domain.entities.usuario import Usuario
from sirue.infrastructure.container import Container
from sirue.presentation.auth_session import (
    cerrar_sesion,
    obtener_usuario_actual,
)


def asegurar_usuario_activo(container: Container) -> Optional[Usuario]:
    """Obtiene el usuario autenticado activo en la sesión o None si no ha iniciado sesión."""
    return obtener_usuario_actual(container)


def crear_header(container: Container, active_tab: str = "inicio") -> None:
    """Renderiza la barra de navegación institucional superior con soporte responsivo total.

    En laptop y pantallas de escritorio (zoom al 100% o superior) muestra la barra horizontal
    con enlaces directos. En móviles y pantallas estrechas provee un menú hamburguesa accesible.

    Args:
        container: Contenedor de dependencias.
        active_tab: Pestaña o ruta actualmente activa para resaltar en la interfaz.
    """
    usuario = obtener_usuario_actual(container)
    es_admin = usuario.es_admin() if usuario else False
    notif_count = (
        container.notification_service.contar_no_leidas(usuario.id) if usuario else 0
    )

    with ui.header().classes(
        "bg-gradient-to-r from-blue-950 via-indigo-900 to-blue-900 text-white shadow-md "
        "px-3 md:px-6 py-2 flex items-center justify-between sticky top-0 z-50 w-full border-b border-blue-800/60"
    ):
        # 1. Identidad Institucional y Logo
        with ui.row().classes("items-center gap-2 md:gap-3 shrink-0"):
            ui.icon("school", size="md").classes("text-amber-400")
            with ui.link(target="/").classes("no-underline text-white"):
                with ui.column().classes("gap-0"):
                    ui.label("SIRUE · UAB").classes(
                        "font-black text-lg md:text-xl tracking-wider text-white leading-tight"
                    )
                    ui.label("Campus Universitario").classes(
                        "text-[10px] text-blue-200 hidden sm:block font-medium tracking-wider uppercase"
                    )

        # 2. Navegación Desktop / Laptop (Visible siempre en pantallas medianas y grandes, zoom al 100%)
        if usuario:
            with ui.row().classes("hidden md:flex items-center gap-1.5 flex-wrap"):

                def _btn_nav(nombre: str, icon: str, ruta: str, tab_id: str, badge_val: int = 0) -> None:
                    esta_activo = (active_tab == tab_id)
                    btn_clase = "bg-blue-800/90 text-white font-bold shadow-sm" if esta_activo else "text-blue-100 hover:bg-white/10"
                    with ui.button(
                        nombre,
                        icon=icon,
                        on_click=lambda r=ruta: ui.navigate.to(r),
                    ).props(f"flat dense no-caps size=sm").classes(f"px-3 py-1.5 rounded-lg {btn_clase}"):
                        if badge_val > 0:
                            ui.badge(str(badge_val), color="orange").props("floating dense")

                _btn_nav("Inicio / Reportes", "home", "/", "inicio")
                _btn_nav("Reportar Perdido", "search", "/reportar-perdido", "perdido")
                _btn_nav("Reportar Encontrado", "add_a_photo", "/reportar-encontrado", "encontrado")
                _btn_nav("Coincidencias", "auto_awesome", "/coincidencias", "coincidencias", notif_count)
                _btn_nav("Mis Reportes", "inventory_2", "/mis-reportes", "mis_reportes")

                if es_admin:
                    esta_activo_admin = (active_tab == "admin")
                    admin_clase = "bg-amber-600 text-white font-bold shadow-sm" if esta_activo_admin else "text-amber-300 hover:bg-amber-500/20"
                    ui.button(
                        "Panel Admin",
                        icon="admin_panel_settings",
                        on_click=lambda: ui.navigate.to("/admin"),
                    ).props("flat dense no-caps size=sm").classes(f"px-3 py-1.5 rounded-lg {admin_clase}")

        # 3. Acciones de Usuario / Perfil y Menú Móvil
        with ui.row().classes("items-center gap-2 shrink-0"):
            if usuario:
                # Indicador de Rol (Badge)
                if es_admin:
                    ui.badge("ADMIN", color="amber-8").props("rounded dense").classes("hidden lg:inline-flex text-[10px] font-bold px-2 py-0.5")
                else:
                    ui.badge("ESTUDIANTE", color="blue-6").props("rounded dense").classes("hidden lg:inline-flex text-[10px] font-bold px-2 py-0.5")

                # Menú desplegable de Perfil
                with ui.button(icon="account_circle").props("flat round color=white size=md").tooltip("Perfil y sesión"):
                    with ui.menu().classes("p-3 min-w-72 rounded-xl shadow-xl border border-gray-100"):
                        ui.label("Usuario Conectado").classes("text-[10px] font-bold text-gray-400 uppercase tracking-wider")
                        with ui.row().classes("items-center justify-between mt-1 mb-1"):
                            ui.label(usuario.nombre).classes("font-extrabold text-gray-800 text-sm")
                            b_col = "amber-9" if es_admin else "blue-7"
                            ui.badge(usuario.rol.value.upper(), color=b_col).props("dense text-[10px]")

                        ui.label(usuario.email).classes("text-xs text-gray-600 font-mono")
                        if getattr(usuario, "telefono", ""):
                            with ui.row().classes("items-center gap-1 text-xs text-gray-500 mt-1"):
                                ui.icon("call", size="xs").classes("text-green-600")
                                ui.label(f"Tel/WhatsApp: {usuario.telefono}")

                        ui.separator().classes("my-2")

                        if es_admin:
                            ui.button(
                                "Panel Administrativo",
                                icon="admin_panel_settings",
                                on_click=lambda: ui.navigate.to("/admin"),
                            ).props("flat dense align=left class=w-full text-amber-900")

                        ui.button(
                            "Mis Reportes Publicados",
                            icon="inventory_2",
                            on_click=lambda: ui.navigate.to("/mis-reportes"),
                        ).props("flat dense align=left class=w-full text-gray-700")

                        ui.button(
                            "Centro de Coincidencias",
                            icon="auto_awesome",
                            on_click=lambda: ui.navigate.to("/coincidencias"),
                        ).props("flat dense align=left class=w-full text-gray-700")

                        ui.separator().classes("my-2")

                        ui.button(
                            "Cerrar Sesión",
                            icon="logout",
                            on_click=cerrar_sesion,
                        ).props("flat dense align=left class=w-full text-red-600 font-bold")

                # Botón de menú hamburguesa (Visible en móviles y pantallas estrechas)
                with ui.button(icon="menu").classes("md:hidden").props("flat round color=white size=md"):
                    with ui.menu().classes("p-2 min-w-60 rounded-xl shadow-xl"):
                        ui.label("Navegación SIRUE").classes("text-[10px] font-bold text-gray-400 uppercase px-3 py-1")
                        ui.button("Inicio / Reportes", icon="home", on_click=lambda: ui.navigate.to("/")).props("flat align=left class=w-full")
                        ui.button("Reportar Perdido", icon="search", on_click=lambda: ui.navigate.to("/reportar-perdido")).props("flat align=left class=w-full")
                        ui.button("Reportar Encontrado", icon="add_a_photo", on_click=lambda: ui.navigate.to("/reportar-encontrado")).props("flat align=left class=w-full")
                        with ui.button("Coincidencias", icon="auto_awesome", on_click=lambda: ui.navigate.to("/coincidencias")).props("flat align=left class=w-full"):
                            if notif_count > 0:
                                ui.badge(str(notif_count), color="orange").props("dense")
                        ui.button("Mis Reportes", icon="inventory_2", on_click=lambda: ui.navigate.to("/mis-reportes")).props("flat align=left class=w-full")
                        if es_admin:
                            ui.button("Panel Admin", icon="admin_panel_settings", on_click=lambda: ui.navigate.to("/admin")).props("flat align=left class=w-full text-amber-800 font-bold")
                        ui.separator().classes("my-1")
                        ui.button("Cerrar Sesión", icon="logout", on_click=cerrar_sesion).props("flat align=left class=w-full text-red-600")

            else:
                # Si no está autenticado, enlace a iniciar sesión
                ui.button(
                    "Iniciar Sesión",
                    icon="login",
                    on_click=lambda: ui.navigate.to("/login"),
                ).props("unelevated color=amber-500 text-color=grey-9 size=sm font-bold").classes("shadow-sm")
