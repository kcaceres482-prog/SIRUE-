"""Página de inicio (Dashboard y Listado de Reportes) para SIRUE."""

from __future__ import annotations

from nicegui import ui

from sirue.application.dtos.reporte_dto import ReporteOutputDTO
from sirue.domain.entities.reporte_objeto import TipoReporte
from sirue.infrastructure.container import Container
from sirue.presentation.components.header import crear_header
from sirue.presentation.components.modal_detalle_reporte import abrir_modal_detalle_reporte


def crear_pagina_home(container: Container) -> None:
    """Construye y renderiza la vista principal de SIRUE."""
    crear_header(container, active_tab="inicio")

    # Contenedor central responsivo
    with ui.column().classes("w-full max-w-6xl mx-auto p-4 gap-6"):

        # Banner de bienvenida y accesos rápidos
        with ui.card().classes(
            "w-full bg-gradient-to-r from-blue-900 to-indigo-900 text-white "
            "p-6 rounded-2xl shadow-lg border-0"
        ):
            with ui.row().classes("w-full justify-between items-center flex-wrap gap-4"):
                with ui.column().classes("gap-1 max-w-xl"):
                    ui.label("Sistema de Objetos Perdidos y Encontrados").classes(
                        "text-2xl md:text-3xl font-extrabold tracking-tight"
                    )
                    ui.label(
                        "Plataforma inteligente y comunitaria para la recuperación de pertenencias dentro del campus universitario."
                    ).classes("text-blue-100 text-sm md:text-base leading-relaxed")

                with ui.row().classes("gap-3 flex-wrap"):
                    ui.button(
                        "Reportar Pérdida",
                        icon="search",
                        on_click=lambda: ui.navigate.to("/reportar-perdido"),
                    ).props("unelevated color=negative size=md").classes("px-4 py-2 font-bold shadow-md")

                    ui.button(
                        "Registrar Hallazgo",
                        icon="add_a_photo",
                        on_click=lambda: ui.navigate.to("/reportar-encontrado"),
                    ).props("unelevated color=positive size=md").classes("px-4 py-2 font-bold shadow-md")

        # Cargar datos desde base de datos
        reportes_activos_dto: list[ReporteOutputDTO] = []
        num_perdidos = 0
        num_encontrados = 0
        num_coincidencias = 0

        with container.database.get_session() as session:
            r_repo = container.reporte_repository(session)
            u_repo = container.usuario_repository(session)
            c_repo = container.coincidencia_repository(session)

            perdidos = r_repo.listar_activos_por_tipo(TipoReporte.PERDIDO)
            encontrados = r_repo.listar_activos_por_tipo(TipoReporte.ENCONTRADO)
            coincidencias = c_repo.listar_pendientes()

            num_perdidos = len(perdidos)
            num_encontrados = len(encontrados)
            num_coincidencias = len(coincidencias)

            todos_activos = perdidos + encontrados
            for r in todos_activos:
                usr = u_repo.obtener_por_id(r.usuario_id)
                nombre_u = usr.nombre if usr else "Estudiante"
                reportes_activos_dto.append(
                    ReporteOutputDTO(
                        id=r.id,
                        tipo=r.tipo.value,
                        titulo=r.titulo,
                        descripcion=r.descripcion,
                        categoria=r.categoria.value,
                        referencia=r.ubicacion.referencia_interna,
                        fecha_hora_incidente=r.fecha_hora_incidente.valor.isoformat(),
                        usuario_id=r.usuario_id,
                        nombre_usuario=nombre_u,
                        foto_ruta=r.foto_ruta,
                        palabras_clave=r.palabras_clave,
                        estado=r.estado.value,
                        fecha_creacion=r.fecha_creacion.isoformat(),
                    )
                )

        # Tarjetas Métricas / Estadísticas del Campus
        with ui.grid().classes("w-full grid-cols-2 md:grid-cols-4 gap-4"):
            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("inventory_2", size="md").classes("text-blue-600")
                ui.label(str(len(reportes_activos_dto))).classes("text-2xl font-bold text-gray-800")
                ui.label("Reportes Activos").classes("text-xs text-gray-500 font-medium")

            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("help_outline", size="md").classes("text-red-500")
                ui.label(str(num_perdidos)).classes("text-2xl font-bold text-gray-800")
                ui.label("Objetos Perdidos").classes("text-xs text-gray-500 font-medium")

            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("check_circle", size="md").classes("text-green-600")
                ui.label(str(num_encontrados)).classes("text-2xl font-bold text-gray-800")
                ui.label("Objetos Encontrados").classes("text-xs text-gray-500 font-medium")

            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("auto_awesome", size="md").classes("text-amber-500")
                ui.label(str(num_coincidencias)).classes("text-2xl font-bold text-gray-800")
                ui.label("Coincidencias Detectadas").classes("text-xs text-gray-500 font-medium")

        # Últimos Reportes Registrados
        with ui.column().classes("w-full gap-3"):
            ui.label("Últimos Reportes Registrados").classes("font-bold text-lg text-gray-800")

            if not reportes_activos_dto:
                with ui.card().classes("w-full p-8 text-center text-gray-400 rounded-xl bg-white border border-dashed"):
                    ui.icon("inbox", size="xl").classes("mx-auto mb-2 text-gray-300")
                    ui.label("No hay reportes activos en este momento.").classes("font-medium")
                    ui.label("Sé el primero en registrar un objeto perdido o encontrado en el campus.").classes("text-xs")
            else:
                with ui.grid().classes("w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"):
                    for r in reportes_activos_dto[:6]:
                        with ui.card().classes(
                            "p-4 rounded-xl bg-white shadow-sm border border-gray-100 "
                            "hover:shadow-md transition-all flex flex-col justify-between"
                        ):
                            with ui.column().classes("gap-2 w-full"):
                                with ui.row().classes("justify-between items-start w-full"):
                                    badge_color = "red" if r.tipo == "PERDIDO" else "green"
                                    ui.badge(r.tipo, color=badge_color).props("rounded text-xs")
                                    ui.label(r.fecha_hora_incidente[:10]).classes("text-xs text-gray-400")

                                ui.label(r.titulo).classes("font-bold text-base text-gray-800 line-clamp-1")
                                ui.label(r.descripcion).classes("text-xs text-gray-600 line-clamp-2")

                                with ui.row().classes("items-center gap-1 text-xs text-gray-500 pt-1"):
                                    ui.icon("place", size="xs").classes("text-gray-400")
                                    ui.label(r.referencia).classes("line-clamp-1")

                                if r.foto_ruta:
                                    img_el = ui.image(f"/{r.foto_ruta}").classes(
                                        "h-36 w-full object-cover rounded-lg mt-2 cursor-pointer hover:opacity-90 transition-opacity"
                                    )
                                    img_el.on("click", lambda _=None, rep=r: abrir_modal_detalle_reporte(rep, container))
                                    img_el.tooltip("Haz clic para ver la imagen completa y opciones de contacto")

                            with ui.row().classes("justify-between items-center w-full pt-3 mt-2 border-t border-gray-100 text-xs text-gray-500"):
                                ui.label(f"Por: {r.nombre_usuario}").classes("line-clamp-1")
                                with ui.row().classes("items-center gap-2"):
                                    ui.badge(r.categoria, color="blue-grey-2", text_color="grey-8").props("dense text-[10px]")
                                    ui.button(
                                        "Ver detalles",
                                        icon="visibility",
                                        on_click=lambda _=None, rep=r: abrir_modal_detalle_reporte(rep, container),
                                    ).props("flat dense color=primary size=xs no-caps font-bold")
