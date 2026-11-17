"""Componente modal reutilizable para ver imagen completa, ficha técnica y contacto directo."""

from __future__ import annotations

import re
from typing import Any, Optional
import urllib.parse

from nicegui import ui

from sirue.domain.entities.usuario import Usuario
from sirue.infrastructure.container import Container


def normalizar_telefono_whatsapp(telefono: str) -> str:
    """Normaliza un número boliviano para WhatsApp (código 591)."""
    if not telefono:
        return ""
    solo_digitos = re.sub(r"\D", "", telefono)
    if not solo_digitos:
        return ""
    # Si tiene 8 dígitos (formato estándar móvil en Bolivia: 6XXXXXXX o 7XXXXXXX)
    if len(solo_digitos) == 8:
        return f"591{solo_digitos}"
    # Si empieza con 591 y tiene 11 dígitos
    if len(solo_digitos) == 11 and solo_digitos.startswith("591"):
        return solo_digitos
    return solo_digitos


def generar_enlace_whatsapp(
    telefono: str, titulo_reporte: str, tipo_reporte: str = "objeto"
) -> str:
    """Genera la URL directa de wa.me con mensaje prellenado."""
    num_wa = normalizar_telefono_whatsapp(telefono)
    if not num_wa:
        return ""
    tipo_txt = "perdido" if "PERDIDO" in tipo_reporte.upper() else "encontrado"
    mensaje = f"Hola, te contacto desde la plataforma SIRUE UAB sobre el {tipo_txt} '{titulo_reporte}'."
    msg_encoded = urllib.parse.quote(mensaje)
    return f"https://wa.me/{num_wa}?text={msg_encoded}"


def renderizar_bloque_contacto(
    nombre_contacto: str,
    email_contacto: str,
    telefono_contacto: str = "",
    titulo_reporte: str = "Objeto",
    tipo_reporte: str = "REPORTE",
) -> None:
    """Renderiza la sección 'Contactar al reportante' con WhatsApp, copia de teléfono y mailto."""
    with ui.card().classes(
        "w-full p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl gap-3"
    ):
        with ui.row().classes("items-center gap-2"):
            ui.icon("connect_without_contact", size="sm").classes("text-blue-700")
            ui.label("Contactar al Reportante").classes("font-bold text-gray-800 text-sm")

        with ui.column().classes("gap-1 text-xs text-gray-700"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("person", size="xs").classes("text-gray-500")
                ui.label(f"Publicado por: {nombre_contacto}").classes("font-semibold")

            with ui.row().classes("items-center gap-2 flex-wrap"):
                ui.icon("mail", size="xs").classes("text-gray-500")
                ui.label(email_contacto).classes("font-mono text-gray-600")

            if telefono_contacto:
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.icon("phone", size="xs").classes("text-gray-500")
                    ui.label(f"Teléfono / WhatsApp: {telefono_contacto}").classes("font-mono font-bold text-gray-800")

        # Botones de contacto directo
        with ui.row().classes("items-center gap-2 flex-wrap pt-1"):
            # 1. WhatsApp
            link_wa = generar_enlace_whatsapp(telefono_contacto, titulo_reporte, tipo_reporte)
            if link_wa:
                ui.button(
                    "Abrir WhatsApp",
                    icon="chat",
                    on_click=lambda url=link_wa: ui.navigate.to(url, new_tab=True),
                ).props("unelevated color=positive size=sm font-bold").classes("shadow-sm")

            # 2. Copiar número
            if telefono_contacto:
                def copiar_tel(t=telefono_contacto):
                    ui.run_javascript(f'navigator.clipboard.writeText("{t}");')
                    ui.notify(f"Número {t} copiado al portapapeles.", type="info")

                ui.button(
                    "Copiar Teléfono",
                    icon="content_copy",
                    on_click=copiar_tel,
                ).props("outline color=grey-8 size=sm")

            # 3. Enviar correo
            asunto = urllib.parse.quote(f"SIRUE UAB: Consulta sobre {titulo_reporte}")
            mail_url = f"mailto:{email_contacto}?subject={asunto}"
            ui.button(
                "Enviar Correo",
                icon="mail",
                on_click=lambda url=mail_url: ui.navigate.to(url, new_tab=True),
            ).props("outline color=primary size=sm")


def abrir_modal_detalle_reporte(
    reporte: Any,
    container: Container,
    usuario_dueno: Optional[Usuario] = None,
) -> None:
    """Abre un modal amplio con visor de imagen completa, detalles y contacto."""
    # Extraer atributos compatibles con DTO o Entidad
    rep_id = getattr(reporte, "id", "")
    titulo = getattr(reporte, "titulo", "Reporte")
    descripcion = getattr(reporte, "descripcion", "")
    tipo = getattr(reporte, "tipo", "")
    tipo_str = tipo.value if hasattr(tipo, "value") else str(tipo)
    categoria = getattr(reporte, "categoria", "")
    cat_str = categoria.value if hasattr(categoria, "value") else str(categoria)
    foto_ruta = getattr(reporte, "foto_ruta", None)

    # Ubicación
    ubicacion = getattr(reporte, "ubicacion", None)
    if ubicacion and hasattr(ubicacion, "referencia_interna"):
        ref_interna = ubicacion.referencia_interna
    else:
        ref_interna = getattr(reporte, "referencia", "Campus UAB")

    # Fecha
    f_incidente = getattr(reporte, "fecha_hora_incidente", None)
    if f_incidente and hasattr(f_incidente, "valor"):
        fecha_txt = f_incidente.valor.strftime("%Y-%m-%d %H:%M")
    elif isinstance(f_incidente, str):
        fecha_txt = f_incidente[:16].replace("T", " ")
    else:
        fecha_txt = str(f_incidente or "")[:16]

    # Estado
    estado = getattr(reporte, "estado", "")
    estado_str = estado.value if hasattr(estado, "value") else str(estado)

    # Datos del dueño
    usuario_id = getattr(reporte, "usuario_id", None)
    nombre_dueno = getattr(reporte, "nombre_usuario", "Usuario de la UAB")
    email_dueno = "contacto@uab.edu.bo"
    telefono_dueno = ""

    if not usuario_dueno and usuario_id:
        try:
            with container.database.get_session() as s:
                u = container.usuario_repository(s).obtener_por_id(usuario_id)
                if u:
                    usuario_dueno = u
        except Exception:
            pass

    if usuario_dueno:
        nombre_dueno = usuario_dueno.nombre
        email_dueno = usuario_dueno.email
        telefono_dueno = getattr(usuario_dueno, "telefono", "") or ""

    with ui.dialog() as dlg, ui.card().classes(
        "p-5 w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl gap-4 shadow-2xl border border-gray-100"
    ):
        # Cabecera del modal con botón de cierre
        with ui.row().classes("w-full justify-between items-center"):
            with ui.row().classes("items-center gap-2"):
                b_color = "red" if tipo_str == "PERDIDO" else "green"
                ui.badge(tipo_str, color=b_color).props("rounded text-xs")
                ui.badge(cat_str, color="blue-grey-2", text_color="grey-8").props("dense text-xs")
                est_color = "positive" if estado_str in ("ACTIVO", "RECUPERADO", "RESUELTO") else "grey-7"
                ui.badge(estado_str, color=est_color).props("outline text-xs")

            ui.button(icon="close", on_click=dlg.close).props("flat round dense size=sm color=grey-7")

        # Imagen en alta resolución / tamaño completo
        if foto_ruta:
            with ui.column().classes("w-full items-center bg-gray-900/5 p-2 rounded-xl border border-gray-100"):
                ui.image(f"/{foto_ruta}").classes("w-full max-h-80 object-contain rounded-lg")
                ui.label("Fotografía original del reporte").classes("text-[10px] text-gray-400 mt-1")

        # Ficha técnica
        with ui.column().classes("gap-1.5 w-full"):
            ui.label(titulo).classes("text-xl font-black text-gray-900")
            if descripcion:
                ui.label(descripcion).classes("text-sm text-gray-700 bg-gray-50 p-3 rounded-lg border border-gray-100 whitespace-pre-wrap")

            with ui.grid().classes("grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-gray-600 pt-2"):
                with ui.row().classes("items-center gap-1.5"):
                    ui.icon("place", size="xs").classes("text-red-500")
                    ui.label(f"Lugar: {ref_interna}").classes("font-medium")

                with ui.row().classes("items-center gap-1.5"):
                    ui.icon("schedule", size="xs").classes("text-blue-500")
                    ui.label(f"Fecha: {fecha_txt}").classes("font-medium")

        # Sección de contacto directo
        renderizar_bloque_contacto(
            nombre_contacto=nombre_dueno,
            email_contacto=email_dueno,
            telefono_contacto=telefono_dueno,
            titulo_reporte=titulo,
            tipo_reporte=tipo_str,
        )

        with ui.row().classes("w-full justify-end pt-2"):
            ui.button("Cerrar", on_click=dlg.close).props("unelevated color=grey-3 text-color=grey-9")

    dlg.open()
