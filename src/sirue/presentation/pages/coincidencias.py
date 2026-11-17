"""Página del Centro Inteligente de Coincidencias para SIRUE."""

from __future__ import annotations

from nicegui import ui

from sirue.domain.entities.coincidencia import EstadoCoincidencia
from sirue.domain.entities.reporte_objeto import TipoReporte
from sirue.infrastructure.container import Container
from sirue.presentation.components.header import (
    asegurar_usuario_activo,
    crear_header,
)
from sirue.presentation.components.modal_detalle_reporte import (
    abrir_modal_detalle_reporte,
    renderizar_bloque_contacto,
)


def crear_pagina_coincidencias(container: Container) -> None:
    """Construye la vista central de detección y resolución de coincidencias."""
    crear_header(container, active_tab="coincidencias")
    usuario_actual = asegurar_usuario_activo(container)
    if not usuario_actual:
        ui.navigate.to("/login")
        return

    with ui.column().classes("w-full max-w-5xl mx-auto p-4 gap-6"):

        # Cabecera
        with ui.row().classes("w-full justify-between items-center flex-wrap gap-4"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("auto_awesome", size="lg").classes("text-amber-500")
                with ui.column().classes("gap-0"):
                    ui.label("Centro Inteligente de Coincidencias").classes("text-2xl font-extrabold text-gray-800")
                    ui.label(
                        "Motor heurístico de afinidad que cruza categoría, similitud léxica difusa y proximidad temporal."
                    ).classes("text-xs text-gray-500")

            def ejecutar_reproceso():
                with container.database.get_session() as s:
                    uc = container.procesar_coincidencias_use_case(s)
                    nuevas = uc.reprocesar_coincidencias(umbral=0.4)
                ui.notify(f"Proceso completado. Se generaron {len(nuevas)} nuevas coincidencias.", type="positive")
                ui.navigate.to("/coincidencias")

            ui.button("Escanear Nuevas Coincidencias", icon="sync", on_click=ejecutar_reproceso).props(
                "outline color=primary size=sm"
            )

        # Cargar todas las coincidencias pendientes de la base de datos
        coincidencias_data = []
        with container.database.get_session() as session:
            c_repo = container.coincidencia_repository(session)
            r_repo = container.reporte_repository(session)
            u_repo = container.usuario_repository(session)

            pendientes = c_repo.listar_pendientes()

            for c in pendientes:
                p = r_repo.obtener_por_id(c.reporte_perdido_id)
                e = r_repo.obtener_por_id(c.reporte_encontrado_id)
                if p and e:
                    u_perdedor = u_repo.obtener_por_id(p.usuario_id)
                    u_encontrador = u_repo.obtener_por_id(e.usuario_id)
                    coincidencias_data.append(
                        {
                            "coincidencia": c,
                            "perdido": p,
                            "encontrado": e,
                            "usuario_perdido_obj": u_perdedor,
                            "usuario_encontrado_obj": u_encontrador,
                            "usuario_perdido": u_perdedor.nombre if u_perdedor else "Estudiante",
                            "usuario_encontrado": u_encontrador.nombre if u_encontrador else "Estudiante",
                        }
                    )

        if not coincidencias_data:
            with ui.card().classes("w-full p-12 text-center text-gray-400 rounded-2xl bg-white shadow-sm border border-dashed"):
                ui.icon("check_circle", size="xl").classes("mx-auto mb-2 text-green-500")
                ui.label("No hay coincidencias pendientes en este momento.").classes("font-bold text-lg text-gray-700")
                ui.label(
                    "El motor se ejecuta automáticamente cuando se registra un objeto perdido o encontrado en el campus."
                ).classes("text-xs text-gray-500 max-w-md mx-auto mb-4")
                ui.button("Volver al Inicio", on_click=lambda: ui.navigate.to("/")).props(
                    "unelevated color=primary size=sm"
                )
            return

        # Listado de tarjetas de afinidad
        with ui.column().classes("w-full gap-5"):
            for item in coincidencias_data:
                c = item["coincidencia"]
                p = item["perdido"]
                e = item["encontrado"]
                u_p = item["usuario_perdido"]
                u_e = item["usuario_encontrado"]
                u_p_obj = item["usuario_perdido_obj"]
                u_e_obj = item["usuario_encontrado_obj"]

                puntuacion_pct = int(c.puntuacion * 100)
                color_barra = "green" if puntuacion_pct >= 75 else ("amber" if puntuacion_pct >= 50 else "blue")

                with ui.card().classes(
                    "w-full p-6 rounded-2xl bg-white shadow-md border border-gray-100 flex flex-col gap-4"
                ):
                    # Cabecera de la tarjeta con porcentaje de afinidad
                    with ui.row().classes("w-full justify-between items-center border-b border-gray-100 pb-3 flex-wrap gap-2"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.circular_progress(
                                value=c.puntuacion,
                                min=0.0,
                                max=1.0,
                                color=color_barra,
                                size="52px",
                                show_value=False,
                            ).props("thickness=0.25 track-color=grey-3"):
                                ui.label(f"{puntuacion_pct}%").classes("text-xs font-bold text-gray-800")

                            with ui.column().classes("gap-0"):
                                ui.label(f"Afinidad del {puntuacion_pct}%").classes("font-extrabold text-base text-gray-800")
                                ui.label("Alta probabilidad de pertenencia entre estos reportes").classes("text-xs text-gray-500")

                        # Desglose y etiquetas explicativas del motor
                        detalles = c.detalles or {}
                        etiquetas = detalles.get("etiquetas") or []
                        with ui.column().classes("items-end gap-1"):
                            with ui.row().classes("gap-1 flex-wrap text-xs"):
                                ui.badge(f"Categoría: {detalles.get('categoria', 0):.0%}", color="indigo-1", text_color="indigo-9").props("dense")
                                ui.badge(f"Texto: {detalles.get('palabras_clave', 0):.0%}", color="blue-1", text_color="blue-9").props("dense")
                                ui.badge(f"Ubicación: {detalles.get('ubicacion', 0):.0%}", color="green-1", text_color="green-9").props("dense")
                                ui.badge(f"Tiempo: {detalles.get('tiempo', 0):.0%}", color="orange-1", text_color="orange-9").props("dense")

                            if etiquetas:
                                with ui.row().classes("gap-1 flex-wrap"):
                                    for etiq in etiquetas:
                                        ui.badge(etiq, color="amber-7").props("rounded text-[10px]")

                    # Comparativa lado a lado (Objeto Perdido vs Objeto Encontrado)
                    with ui.grid().classes("w-full grid-cols-1 md:grid-cols-2 gap-4 my-2"):

                        # Columna 1: Objeto Perdido
                        with ui.card().classes("p-4 rounded-xl bg-red-50/50 border border-red-100 flex flex-col justify-between"):
                            with ui.column().classes("gap-1 w-full"):
                                with ui.row().classes("justify-between items-center w-full mb-1"):
                                    ui.badge("PÉRDIDA REPORTADA", color="red").props("dense text-xs")
                                    ui.label(f"Por: {u_p}").classes("text-xs text-gray-500")

                                ui.label(p.titulo).classes("font-bold text-base text-gray-800")
                                ui.label(p.descripcion).classes("text-xs text-gray-600 mb-2 whitespace-pre-wrap")

                                with ui.column().classes("gap-1 text-xs text-gray-500 border-t border-red-100 pt-2"):
                                    ui.label(f"📍 Lugar: {p.ubicacion.referencia_interna}")
                                    ui.label(f"🕒 Fecha: {p.fecha_hora_incidente.valor.strftime('%Y-%m-%d %H:%M')}")

                            with ui.row().classes("w-full justify-end pt-2"):
                                ui.button(
                                    "Ver ficha completa",
                                    icon="visibility",
                                    on_click=lambda _=None, rep=p, u_obj=u_p_obj: abrir_modal_detalle_reporte(rep, container, u_obj),
                                ).props("flat dense color=red-9 size=xs font-bold no-caps")

                        # Columna 2: Objeto Encontrado
                        with ui.card().classes("p-4 rounded-xl bg-green-50/50 border border-green-100 flex flex-col justify-between"):
                            with ui.column().classes("gap-1 w-full"):
                                with ui.row().classes("justify-between items-center w-full mb-1"):
                                    ui.badge("HALLAZGO EN CAMPUS", color="green").props("dense text-xs")
                                    ui.label(f"Por: {u_e}").classes("text-xs text-gray-500")

                                ui.label(e.titulo).classes("font-bold text-base text-gray-800")
                                ui.label(e.descripcion).classes("text-xs text-gray-600 mb-2 whitespace-pre-wrap")

                                if e.foto_ruta:
                                    img_box = ui.image(f"/{e.foto_ruta}").classes(
                                        "w-full h-36 object-cover rounded-lg my-1 shadow-sm cursor-pointer hover:opacity-90 transition-opacity"
                                    )
                                    img_box.on("click", lambda _=None, rep=e, u_obj=u_e_obj: abrir_modal_detalle_reporte(rep, container, u_obj))
                                    img_box.tooltip("Haz clic para ver la imagen completa")

                                with ui.column().classes("gap-1 text-xs text-gray-500 border-t border-green-100 pt-2"):
                                    ui.label(f"📍 Lugar: {e.ubicacion.referencia_interna}")
                                    ui.label(f"🕒 Fecha: {e.fecha_hora_incidente.valor.strftime('%Y-%m-%d %H:%M')}")

                            with ui.row().classes("w-full justify-end pt-2"):
                                ui.button(
                                    "Ver ficha y foto completa",
                                    icon="visibility",
                                    on_click=lambda _=None, rep=e, u_obj=u_e_obj: abrir_modal_detalle_reporte(rep, container, u_obj),
                                ).props("flat dense color=green-9 size=xs font-bold no-caps")

                    # Bloque de contacto con quien encontró el objeto
                    if u_e_obj:
                        renderizar_bloque_contacto(
                            nombre_contacto=u_e_obj.nombre,
                            email_contacto=u_e_obj.email,
                            telefono_contacto=getattr(u_e_obj, "telefono", "") or "",
                            titulo_reporte=e.titulo,
                            tipo_reporte="ENCONTRADO",
                        )

                    # Botones de Acción (Confirmar vs Descartar)
                    with ui.row().classes("w-full justify-between items-center pt-2 border-t border-gray-100 flex-wrap gap-2"):
                        def descartar(cid=c.id):
                            with container.database.get_session() as s:
                                uc = container.procesar_coincidencias_use_case(s)
                                uc.descartar_coincidencia(cid)
                            ui.notify("Coincidencia descartada como falso positivo.", type="info")
                            ui.navigate.to("/coincidencias")

                        def confirmar(cid=c.id):
                            with container.database.get_session() as s:
                                uc = container.procesar_coincidencias_use_case(s)
                                uc.confirmar_coincidencia(cid)
                            ui.notify(
                                "¡Coincidencia confirmada! Ambos reportes han sido marcados como RESUELTOS.",
                                type="positive",
                            )
                            ui.navigate.to("/mis-reportes")

                        ui.button("Descartar Falso Positivo", icon="close", on_click=descartar).props(
                            "flat color=grey-7 size=sm no-caps"
                        )
                        ui.button(
                            "Confirmar y Recuperar Pertenencia",
                            icon="handshake",
                            on_click=confirmar,
                        ).props("unelevated color=positive size=md font-bold shadow-md no-caps")
