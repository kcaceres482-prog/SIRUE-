"""Página para registrar el reporte de un objeto encontrado (Hallazgo)."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import inspect
from typing import Optional

from nicegui import events, ui

from sirue.application.dtos.reporte_dto import ReporteInputDTO
from sirue.domain.exceptions.domain_exceptions import (
    FotoRequeridaError,
    SIRUEDomainError,
    ValidacionError,
)
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.infrastructure.container import Container
from sirue.presentation.components.header import (
    asegurar_usuario_activo,
    crear_header,
)


def crear_pagina_registrar_encontrado(container: Container) -> None:
    """Construye la vista móvil y de escritorio para reportar un hallazgo."""
    crear_header(container, active_tab="encontrado")
    usuario_actual = asegurar_usuario_activo(container)
    if not usuario_actual:
        ui.navigate.to("/login")
        return

    # Almacén de foto en memoria durante el formulario
    foto_subida: dict[str, Optional[bytes]] = {"bytes": None, "nombre": None}

    # Prevención de doble submit
    enviando: dict[str, bool] = {"valor": False}

    with ui.column().classes("w-full max-w-4xl mx-auto p-4 gap-6"):

        # Título y contexto
        with ui.row().classes("items-center gap-3"):
            ui.icon("add_a_photo", size="lg").classes("text-green-600")
            with ui.column().classes("gap-0"):
                ui.label("Registrar Objeto Encontrado").classes("text-2xl font-extrabold text-gray-800")
                ui.label("Ayuda a devolver una pertenencia a su dueño adjuntando una fotografía y ubicación precisa.").classes(
                    "text-xs text-gray-500"
                )

        with ui.card().classes("w-full p-6 rounded-2xl bg-white shadow-sm border border-gray-100"):
            with ui.column().classes("w-full gap-4"):

                # Subida de Fotografía OBLIGATORIA
                with ui.column().classes("w-full gap-1"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("photo_camera", size="sm").classes("text-green-700")
                        ui.label("Fotografía del Objeto Encontrado *").classes("font-bold text-gray-800 text-sm")
                        ui.badge("Obligatorio", color="positive").props("dense text-xs")

                    preview_imagen = ui.image().classes("w-full max-h-48 object-contain rounded-xl bg-gray-50 hidden")

                    async def handle_upload(e: events.UploadEventArguments):
                        try:
                            nombre = "foto_hallazgo.jpg"
                            contenido = b""
                            if hasattr(e, "file") and e.file is not None:
                                nombre = getattr(e.file, "name", "foto_hallazgo.jpg") or "foto_hallazgo.jpg"
                                file_read = getattr(e.file, "read", None)
                                if callable(file_read):
                                    res = file_read()
                                    if inspect.isawaitable(res):
                                        contenido = await res
                                    else:
                                        contenido = res
                            elif hasattr(e, "content") and e.content is not None:
                                nombre = getattr(e, "name", "foto_hallazgo.jpg") or "foto_hallazgo.jpg"
                                if hasattr(e.content, "read"):
                                    res = e.content.read()
                                    if inspect.isawaitable(res):
                                        contenido = await res
                                    else:
                                        contenido = res
                                else:
                                    contenido = bytes(e.content)

                            if not contenido:
                                ui.notify("El archivo subido está vacío o no se pudo leer.", type="warning")
                                return

                            foto_subida["bytes"] = contenido
                            foto_subida["nombre"] = nombre
                            b64 = base64.b64encode(contenido).decode("utf-8")
                            preview_imagen.set_source(f"data:image/jpeg;base64,{b64}")
                            preview_imagen.classes(remove="hidden")
                            ui.notify(f"Foto '{nombre}' cargada correctamente.", type="positive")
                        except Exception as exc:
                            ui.notify(f"Error al procesar la fotografía: {exc}", type="negative")

                    def handle_removed():
                        foto_subida["bytes"] = None
                        foto_subida["nombre"] = None
                        preview_imagen.classes(add="hidden")
                        preview_imagen.set_source("")

                    uploader = ui.upload(
                        label="Toma una foto o sube un archivo (JPG, PNG)",
                        auto_upload=True,
                        max_files=1,
                        on_upload=handle_upload,
                        on_rejected=lambda: ui.notify("Archivo rechazado. Sube una imagen válida.", type="negative"),
                    ).props('accept="image/*" capture="environment" color=positive').classes("w-full")
                    uploader.on("removed", handle_removed)

                # Título del hallazgo
                input_titulo = ui.input(
                    label="¿Qué objeto encontraste? *",
                    placeholder="Ej: Mochila negra encontrada cerca al pasillo",
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
                        label="Fecha y hora del hallazgo *",
                        value=ahora_default,
                    ).props('type=datetime-local outlined').classes("w-full")

                # Lugar / Referencia interna
                input_ref = ui.input(
                    label="Lugar o Referencia interna exacta del hallazgo *",
                    placeholder="Ej: Pasillo B, junto a las bancas frente al Aula A-203",
                ).props("outlined").classes("w-full")

                # Descripción breve
                input_desc = ui.textarea(
                    label="Descripción del estado del objeto y circunstancias",
                    placeholder="Ej: Objeto en buen estado hallado sobre una banca sin personas alrededor...",
                ).props("outlined rows=3").classes("w-full")

                # Botón de Registrar Hallazgo
                def guardar_hallazgo():
                    if enviando["valor"]:
                        return
                    enviando["valor"] = True

                    try:
                        titulo = (input_titulo.value or "").strip()
                        desc = (input_desc.value or "").strip()
                        cat = select_cat.value or "OTRO"
                        ref = (input_ref.value or "").strip()
                        fecha_str = input_fecha.value or ahora_default

                        # Validar fotografía
                        if not foto_subida["bytes"]:
                            ui.notify("Debes adjuntar o tomar una fotografía del objeto encontrado.", type="negative")
                            return

                        if not titulo:
                            ui.notify("Por favor ingresa un título para el hallazgo.", type="negative")
                            return
                        if not ref:
                            ui.notify("Por favor ingresa la referencia del lugar donde lo hallaste.", type="negative")
                            return

                        dto = ReporteInputDTO(
                            titulo=titulo,
                            descripcion=desc,
                            categoria_str=cat,
                            referencia=ref,
                            fecha_hora_str=fecha_str if "Z" in fecha_str or "+" in fecha_str else f"{fecha_str}:00Z",
                            usuario_id=usuario_actual.id,
                            foto_bytes=foto_subida["bytes"],
                            foto_nombre=foto_subida["nombre"] or "hallazgo.jpg",
                        )

                        try:
                            with container.database.get_session() as session:
                                uc = container.registrar_objeto_encontrado_use_case(session)
                                reporte_out, matches = uc.ejecutar(dto)

                            ui.notify(f"Hallazgo '{titulo}' publicado exitosamente.", type="positive")

                            # Diálogo con resultados
                            with ui.dialog() as dialogo, ui.card().classes("p-6 max-w-lg w-full rounded-2xl"):
                                with ui.column().classes("gap-3 w-full text-center items-center"):
                                    ui.icon("celebration", size="xl").classes("text-green-600")
                                    ui.label("¡Hallazgo Registrado con Éxito!").classes("text-xl font-bold text-gray-800")
                                    ui.label(
                                        f"Gracias por colaborar con la comunidad universitaria, {usuario_actual.nombre}."
                                    ).classes("text-xs text-gray-500")

                                    if matches:
                                        ui.separator()
                                        with ui.card().classes("w-full bg-emerald-50 border border-emerald-200 p-3 rounded-xl text-left"):
                                            with ui.row().classes("items-center gap-2"):
                                                ui.icon("auto_awesome", size="sm").classes("text-emerald-700")
                                                ui.label(f"¡Posible dueño encontrado! ({len(matches)} match)").classes(
                                                    "font-bold text-emerald-950 text-sm"
                                                )
                                            ui.label(
                                                f"Coincide con el reporte de '{matches[0].titulo_perdido}' con una afinidad de {matches[0].puntuacion:.0%}."
                                            ).classes("text-xs text-emerald-900 mt-1")

                                        ui.button(
                                            "Ver Centro de Coincidencias",
                                            icon="auto_awesome",
                                            on_click=lambda: ui.navigate.to("/coincidencias"),
                                        ).props("unelevated color=positive class=w-full font-bold")
                                    else:
                                        ui.label(
                                            "El reporte está activo a la espera de que el dueño lo reclame."
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
                    "Publicar Hallazgo en el Campus",
                    icon="cloud_upload",
                    on_click=guardar_hallazgo,
                ).props("unelevated color=positive size=lg").classes("w-full font-bold shadow-md mt-4")
