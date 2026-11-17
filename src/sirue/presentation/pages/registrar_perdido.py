"""Página para registrar el reporte de un objeto perdido."""

from __future__ import annotations

from datetime import datetime, timezone

from nicegui import ui

from sirue.application.dtos.reporte_dto import ReporteInputDTO
from sirue.domain.exceptions.domain_exceptions import (
    DescripcionInsuficienteError,
    SIRUEDomainError,
    ValidacionError,
)
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.infrastructure.container import Container
from sirue.presentation.components.header import (
    asegurar_usuario_activo,
    crear_header,
)


def crear_pagina_registrar_perdido(container: Container) -> None:
    """Construye la vista para que un estudiante registre un objeto perdido."""
    crear_header(container, active_tab="perdido")
    usuario_actual = asegurar_usuario_activo(container)
    if not usuario_actual:
        ui.navigate.to("/login")
        return

    # Prevención de doble submit
    enviando: dict[str, bool] = {"valor": False}

    with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-6"):

        # Título y contexto
        with ui.row().classes("items-center gap-3"):
            ui.icon("search", size="lg").classes("text-red-600")
            with ui.column().classes("gap-0"):
                ui.label("Reportar Objeto Perdido").classes("text-2xl font-extrabold text-gray-800")
                ui.label("Ingresa los detalles exactos para que el motor de afinidad localice coincidencias").classes(
                    "text-xs text-gray-500"
                )

        with ui.card().classes("w-full p-6 rounded-2xl bg-white shadow-sm border border-gray-100"):
            with ui.column().classes("w-full gap-4"):

                # Título del objeto
                input_titulo = ui.input(
                    label="¿Qué objeto perdiste? *",
                    placeholder="Ej: Mochila negra marca Totto con parches",
                ).props("outlined clearable").classes("w-full")

                # Categoría y fecha/hora
                with ui.row().classes("w-full grid grid-cols-1 md:grid-cols-2 gap-4"):
                    categorias = [c.value for c in CategoriaObjeto]
                    select_cat = ui.select(
                        options=categorias,
                        value="MOCHILA",
                        label="Categoría del objeto *",
                    ).props("outlined").classes("w-full")

                    ahora_default = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
                    input_fecha = ui.input(
                        label="Fecha y hora estimada *",
                        value=ahora_default,
                    ).props('type=datetime-local outlined').classes("w-full")

                # Lugar / Referencia interna
                input_ref = ui.input(
                    label="Lugar o Referencia interna en campus *",
                    placeholder="Ej: Aula A-203, Edificio de Ingeniería, segunda fila",
                ).props("outlined").classes("w-full")

                # Descripción
                input_desc = ui.textarea(
                    label="Descripción del objeto (opcional)",
                    placeholder="Describe color, marcas distintivas, contenido interno o estado físico...",
                ).props("outlined rows=4").classes("w-full")

                ui.label(
                    "Nota: Los detalles específicos mejoran la precisión al encontrar coincidencias."
                ).classes("text-xs text-blue-600 font-medium -mt-2")

                # Botón de Guardar
                def guardar_reporte():
                    if enviando["valor"]:
                        return
                    enviando["valor"] = True

                    try:
                        titulo = (input_titulo.value or "").strip()
                        desc = (input_desc.value or "").strip()
                        cat = select_cat.value or "OTRO"
                        ref = (input_ref.value or "").strip()
                        fecha_str = input_fecha.value or ahora_default

                        # Validaciones en cliente
                        if not titulo:
                            ui.notify("Por favor ingresa un título para el reporte.", type="negative")
                            return
                        if not ref:
                            ui.notify("Por favor especifica el lugar o aula de referencia.", type="negative")
                            return

                        dto = ReporteInputDTO(
                            titulo=titulo,
                            descripcion=desc,
                            categoria_str=cat,
                            referencia=ref,
                            fecha_hora_str=fecha_str if "Z" in fecha_str or "+" in fecha_str else f"{fecha_str}:00Z",
                            usuario_id=usuario_actual.id,
                        )

                        try:
                            with container.database.get_session() as session:
                                uc = container.registrar_objeto_perdido_use_case(session)
                                reporte_out, matches = uc.ejecutar(dto)

                            ui.notify(f"Reporte '{titulo}' registrado exitosamente.", type="positive")

                            # Mostrar diálogo con resultados inmediatos de afinidad
                            with ui.dialog() as dialogo, ui.card().classes("p-6 max-w-lg w-full rounded-2xl"):
                                with ui.column().classes("gap-3 w-full text-center items-center"):
                                    ui.icon("check_circle", size="xl").classes("text-green-600")
                                    ui.label("¡Reporte Registrado con Éxito!").classes("text-xl font-bold text-gray-800")
                                    ui.label(
                                        f"Tu reporte ha quedado activo en el campus. Estudiante: {usuario_actual.nombre}"
                                    ).classes("text-xs text-gray-500")

                                    if matches:
                                        ui.separator()
                                        with ui.card().classes("w-full bg-amber-50 border border-amber-200 p-3 rounded-xl text-left"):
                                            with ui.row().classes("items-center gap-2"):
                                                ui.icon("auto_awesome", size="sm").classes("text-amber-600")
                                                ui.label(f"¡Se detectaron {len(matches)} posible(s) coincidencia(s)!").classes(
                                                    "font-bold text-amber-900 text-sm"
                                                )
                                            ui.label(
                                                f"El objeto '{matches[0].titulo_encontrado}' tiene un {matches[0].puntuacion:.0%} de afinidad."
                                            ).classes("text-xs text-amber-800 mt-1")

                                        ui.button(
                                            "Ver Coincidencias",
                                            icon="visibility",
                                            on_click=lambda: ui.navigate.to("/coincidencias"),
                                        ).props("unelevated color=amber-8 class=w-full font-bold")
                                    else:
                                        ui.label(
                                            "No hay hallazgos idénticos en este instante. Te notificaremos automáticamente cuando alguien lo reporte."
                                        ).classes("text-xs text-gray-600 italic")

                                    ui.button("Ir al Inicio", on_click=lambda: ui.navigate.to("/")).props(
                                        "flat class=w-full text-blue-700 font-semibold"
                                    )

                            dialogo.open()

                        except SIRUEDomainError as e:
                            ui.notify(str(e), type="negative")
                        except Exception as ex:
                            ui.notify(f"Error inesperado: {ex}", type="negative")
                    finally:
                        enviando["valor"] = False

                ui.button(
                    "Publicar Reporte de Pérdida",
                    icon="send",
                    on_click=guardar_reporte,
                ).props("unelevated color=negative size=lg").classes("w-full font-bold shadow-md mt-4")
