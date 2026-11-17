"""Página de administración de reportes del usuario actual."""

from __future__ import annotations

from nicegui import ui

from sirue.domain.entities.reporte_objeto import EstadoReporte, TipoReporte
from sirue.infrastructure.container import Container
from sirue.presentation.components.header import (
    asegurar_usuario_activo,
    crear_header,
)
from sirue.presentation.components.modal_detalle_reporte import abrir_modal_detalle_reporte


def crear_pagina_mis_reportes(container: Container) -> None:
    """Construye la vista de historial y gestión de reportes del estudiante."""
    crear_header(container, active_tab="mis_reportes")
    usuario_actual = asegurar_usuario_activo(container)
    if not usuario_actual:
        ui.navigate.to("/login")
        return

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-6"):

        # Encabezado
        with ui.row().classes("w-full justify-between items-center flex-wrap gap-4"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("inventory_2", size="lg").classes("text-blue-700")
                with ui.column().classes("gap-0"):
                    ui.label("Mis Publicaciones en el Campus").classes("text-2xl font-extrabold text-gray-800")
                    ui.label(f"Estudiante activo: {usuario_actual.nombre} ({usuario_actual.email})").classes(
                        "text-xs text-gray-500"
                    )

            with ui.row().classes("gap-2"):
                ui.button(
                    "Nuevo Reporte",
                    icon="add",
                    on_click=lambda: ui.navigate.to("/reportar-perdido"),
                ).props("unelevated color=primary size=sm")

        # Cargar reportes del usuario desde base de datos
        with container.database.get_session() as session:
            r_repo = container.reporte_repository(session)
            reportes = r_repo.listar_por_usuario(usuario_actual.id)

        if not reportes:
            with ui.card().classes("w-full p-12 text-center text-gray-400 rounded-2xl bg-white shadow-sm border border-dashed"):
                ui.icon("folder_open", size="xl").classes("mx-auto mb-2 text-gray-300")
                ui.label("Aún no tienes reportes registrados.").classes("font-bold text-lg text-gray-700")
                ui.label("Si perdiste o encontraste alguna pertenencia en el campus, publícala para iniciar la búsqueda.").classes(
                    "text-xs text-gray-500 max-w-md mx-auto mb-4"
                )
                with ui.row().classes("justify-center gap-3"):
                    ui.button("Perdí un objeto", icon="search", on_click=lambda: ui.navigate.to("/reportar-perdido")).props(
                        "unelevated color=negative size=sm"
                    )
                    ui.button("Encontré un objeto", icon="add_a_photo", on_click=lambda: ui.navigate.to("/reportar-encontrado")).props(
                        "unelevated color=positive size=sm"
                    )
            return

        # Listado de tarjetas de reportes
        with ui.column().classes("w-full gap-4"):
            for r in reportes:
                with ui.card().classes(
                    "w-full p-5 rounded-2xl bg-white shadow-sm border border-gray-100 "
                    "flex flex-col md:flex-row gap-4 items-start md:items-center justify-between"
                ):
                    # Foto si existe
                    if r.foto_ruta:
                        img_card = ui.image(f"/{r.foto_ruta}").classes(
                            "w-full md:w-32 h-32 object-cover rounded-xl shadow-sm cursor-pointer hover:opacity-90 transition-opacity"
                        )
                        img_card.on("click", lambda _=None, rep=r: abrir_modal_detalle_reporte(rep, container, usuario_actual))
                        img_card.tooltip("Haz clic para ver la fotografía completa")

                    # Datos principales
                    with ui.column().classes("gap-1 flex-grow"):
                        with ui.row().classes("items-center gap-2"):
                            val_tipo = r.tipo.value if hasattr(r.tipo, "value") else str(r.tipo)
                            val_est = r.estado.value if hasattr(r.estado, "value") else str(r.estado)
                            val_cat = r.categoria.value if hasattr(r.categoria, "value") else str(r.categoria)

                            badge_tipo_color = "red" if val_tipo == "PERDIDO" else "green"
                            ui.badge(val_tipo, color=badge_tipo_color).props("rounded text-xs")

                            badge_est_color = "positive" if val_est in ("ACTIVO", "RECUPERADO", "RESUELTO") else "grey"
                            ui.badge(val_est, color=badge_est_color).props("outline text-xs")

                            ui.badge(val_cat, color="blue-grey-2", text_color="grey-8").props("dense text-xs")

                        ui.label(r.titulo).classes("font-bold text-lg text-gray-800")
                        ui.label(r.descripcion).classes("text-xs text-gray-600 line-clamp-2 max-w-2xl")

                        with ui.row().classes("items-center gap-4 text-xs text-gray-500 pt-1"):
                            with ui.row().classes("items-center gap-1"):
                                ui.icon("place", size="xs").classes("text-gray-400")
                                ui.label(r.ubicacion.referencia_interna)

                            with ui.row().classes("items-center gap-1"):
                                ui.icon("access_time", size="xs").classes("text-gray-400")
                                ui.label(r.fecha_hora_incidente.valor.strftime("%Y-%m-%d %H:%M"))

                    # Acciones sobre el reporte
                    with ui.column().classes("items-end gap-2 shrink-0"):
                        if r.esta_activo():
                            def resolver(rep_id=r.id):
                                with container.database.get_session() as s:
                                    repo = container.reporte_repository(s)
                                    item = repo.obtener_por_id(rep_id)
                                    if item:
                                        item.marcar_resuelto()
                                        repo.actualizar(item)
                                ui.notify("Reporte marcado como resuelto.", type="info")
                                ui.navigate.to("/mis-reportes")

                            ui.button("Marcar Resuelto", icon="check", on_click=resolver).props(
                                "outline color=positive size=sm"
                            )
                        else:
                            ui.chip("Recuperado / Resuelto", icon="task_alt", color="positive").props("dense text-xs")
