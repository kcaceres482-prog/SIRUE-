"""Página del Panel de Supervisión y Control Administrativo para SIRUE."""

from __future__ import annotations

from nicegui import ui

from sirue.application.dtos.usuario_dto import UsuarioOutputDTO
from sirue.domain.entities.reporte_objeto import EstadoReporte, TipoReporte
from sirue.domain.exceptions.domain_exceptions import (
    AccesoDenegadoError,
    OperacionNoPermitidaError,
    SIRUEDomainError,
    UsuarioNoEncontradoError,
    ValidacionError,
)
from sirue.infrastructure.container import Container
from sirue.presentation.components.header import (
    asegurar_usuario_activo,
    crear_header,
)
from sirue.presentation.components.modal_detalle_reporte import abrir_modal_detalle_reporte


def crear_pagina_admin(container: Container) -> None:
    """Construye la vista de supervisión para usuarios con rol 'admin'."""
    usuario_actual = asegurar_usuario_activo(container)

    # 1. Validación de rol administrativo
    if not usuario_actual or not usuario_actual.es_admin():
        crear_header(container, active_tab="")
        with ui.column().classes("w-full max-w-xl mx-auto p-6 mt-12 items-center text-center gap-4"):
            with ui.card().classes("w-full p-8 rounded-2xl bg-white shadow-md border border-red-100 items-center"):
                ui.icon("gpp_bad", size="xl").classes("text-red-600 mb-2")
                ui.label("Acceso Denegado").classes("text-2xl font-bold text-gray-800")
                ui.label(
                    "Esta sección está reservada exclusivamente para el personal administrativo y de seguridad del campus."
                ).classes("text-sm text-gray-600 mb-4")
                with ui.row().classes("gap-3"):
                    ui.button("Volver al Inicio", icon="home", on_click=lambda: ui.navigate.to("/")).props(
                        "unelevated color=primary"
                    )
                    ui.button("Iniciar Sesión como Admin", icon="login", on_click=lambda: ui.navigate.to("/login")).props(
                        "outline color=primary"
                    )
        return

    # Si es administrador, renderizar el panel completo
    crear_header(container, active_tab="admin")

    # Cargar métricas iniciales
    with container.database.get_session() as session:
        uc_admin = container.gestionar_reporte_admin_use_case(session)
        stats = uc_admin.obtener_estadisticas_globales(usuario_actual.id)

    with ui.column().classes("w-full max-w-6xl mx-auto p-4 gap-6"):

        # Banner de bienvenida administrativo
        with ui.card().classes(
            "w-full bg-gradient-to-r from-amber-700 to-amber-900 text-white "
            "p-6 rounded-2xl shadow-lg border-0"
        ):
            with ui.row().classes("w-full justify-between items-center flex-wrap gap-4"):
                with ui.column().classes("gap-1"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("shield", size="md").classes("text-amber-300")
                        ui.label("Panel de Supervisión Administrativa").classes(
                            "text-2xl md:text-3xl font-extrabold tracking-tight"
                        )
                    ui.label(
                        f"Administrador en turno: {usuario_actual.nombre} ({usuario_actual.email}) — Control y Auditoría"
                    ).classes("text-amber-100 text-sm")

                ui.button(
                    "Actualizar Datos",
                    icon="refresh",
                    on_click=lambda: ui.navigate.to("/admin"),
                ).props("unelevated color=white text-color=amber-9 size=sm").classes("font-bold")

        # Tarjetas de Estadísticas Globales
        with ui.grid().classes("w-full grid-cols-2 md:grid-cols-4 gap-4"):
            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("inventory_2", size="md").classes("text-blue-700")
                lbl_total_rep = ui.label(str(stats["total_reportes"])).classes("text-2xl font-bold text-gray-800")
                ui.label("Total Reportes").classes("text-xs text-gray-500 font-medium")

            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("pending_actions", size="md").classes("text-amber-600")
                lbl_activos = ui.label(str(stats["activos"])).classes("text-2xl font-bold text-gray-800")
                ui.label("Reportes Activos").classes("text-xs text-gray-500 font-medium")

            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("check_circle", size="md").classes("text-green-600")
                lbl_resueltos = ui.label(str(stats["recuperados"])).classes("text-2xl font-bold text-gray-800")
                ui.label("Recuperados / Resueltos").classes("text-xs text-gray-500 font-medium")

            with ui.card().classes("p-4 items-center text-center rounded-xl bg-white shadow-sm border border-gray-100"):
                ui.icon("group", size="md").classes("text-indigo-600")
                lbl_total_users = ui.label(str(stats["total_usuarios"])).classes("text-2xl font-bold text-gray-800")
                ui.label("Usuarios Registrados").classes("text-xs text-gray-500 font-medium")

        # Pestañas: Gestión de Reportes / Gestión de Usuarios
        with ui.tabs().classes("w-full") as tabs:
            tab_reportes = ui.tab("Supervisión de Reportes", icon="table_chart")
            tab_usuarios = ui.tab("Gestión de Usuarios", icon="people")

        with ui.tab_panels(tabs, value=tab_reportes).classes("w-full"):

            # PANEL 1: Supervisión de Reportes
            with ui.tab_panel(tab_reportes).classes("p-0 pt-4 flex flex-col gap-4"):

                estados_disponibles = [e.value for e in EstadoReporte]

                # Filtros interactivos
                with ui.row().classes("gap-3 items-center flex-wrap"):
                    ui.label("Filtros de Auditoría:").classes("text-xs font-semibold text-gray-500 uppercase")
                    filtro_tipo = ui.select(
                        label="Tipo",
                        options=["TODOS", "PERDIDO", "ENCONTRADO"],
                        value="TODOS",
                    ).props("outlined dense").classes("w-40")

                    filtro_estado = ui.select(
                        label="Estado",
                        options=["TODOS"] + estados_disponibles,
                        value="TODOS",
                    ).props("outlined dense").classes("w-44")

                contenedor_lista = ui.column().classes("w-full gap-4")

                def renderizar_reportes():
                    contenedor_lista.clear()
                    t_filtro = None if filtro_tipo.value == "TODOS" else filtro_tipo.value
                    e_filtro = None if filtro_estado.value == "TODOS" else filtro_estado.value

                    with container.database.get_session() as s:
                        uc = container.gestionar_reporte_admin_use_case(s)
                        reportes = uc.listar_reportes_supervision(
                            admin_user_id=usuario_actual.id,
                            tipo_filtro=t_filtro,
                            estado_filtro=e_filtro,
                        )

                    if not reportes:
                        with contenedor_lista:
                            with ui.card().classes("w-full p-8 text-center text-gray-400 rounded-xl bg-white border border-dashed"):
                                ui.icon("search_off", size="lg").classes("mx-auto mb-2 text-gray-300")
                                ui.label("No se encontraron reportes con los filtros seleccionados.").classes("font-medium")
                        return

                    with contenedor_lista:
                        for rep in reportes:
                            with ui.card().classes(
                                "w-full p-4 rounded-xl bg-white shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between"
                            ):
                                if rep.foto_ruta:
                                    img_adm = ui.image(f"/{rep.foto_ruta}").classes(
                                        "w-full md:w-24 h-24 object-cover rounded-lg cursor-pointer hover:opacity-90 shadow-sm"
                                    )
                                    img_adm.on("click", lambda _=None, r=rep: abrir_modal_detalle_reporte(r, container))
                                    img_adm.tooltip("Ver foto original y ficha completa")

                                with ui.column().classes("gap-1 flex-grow"):
                                    with ui.row().classes("items-center gap-2"):
                                        b_color = "red" if rep.tipo == "PERDIDO" else "green"
                                        ui.badge(rep.tipo, color=b_color).props("rounded text-xs")

                                        est_color = "positive" if rep.estado in ("ACTIVO", "RECUPERADO", "RESUELTO") else "grey-7"
                                        ui.badge(rep.estado, color=est_color).props("outline text-xs")

                                        ui.badge(rep.categoria, color="blue-grey-2", text_color="grey-8").props("dense text-xs")

                                    ui.label(rep.titulo).classes("font-bold text-base text-gray-800")
                                    ui.label(rep.descripcion).classes("text-xs text-gray-600 line-clamp-2 max-w-xl")

                                    with ui.row().classes("items-center gap-3 text-xs text-gray-400 pt-1"):
                                        ui.label(f"Estudiante: {rep.nombre_usuario}")
                                        ui.label(f"Ubicación: {rep.referencia}")
                                        ui.label(f"Fecha: {rep.fecha_hora_incidente[:10]}")

                                # Selector administrativo de cambio de estado
                                with ui.row().classes("items-center gap-2 shrink-0"):
                                    opciones_fila = list(estados_disponibles)
                                    val_estado_actual = str(rep.estado).upper().strip()
                                    if val_estado_actual not in opciones_fila:
                                        opciones_fila.append(val_estado_actual)

                                    sel_estado = ui.select(
                                        options=opciones_fila,
                                        value=val_estado_actual,
                                    ).props("dense outlined").classes("w-36")

                                    def cambiar_est(r_id=rep.id, sel=sel_estado):
                                        try:
                                            with container.database.get_session() as s:
                                                uc = container.gestionar_reporte_admin_use_case(s)
                                                uc.cambiar_estado_reporte(r_id, sel.value, usuario_actual.id)
                                            ui.notify(f"Estado de reporte actualizado a {sel.value}", type="positive")
                                            renderizar_reportes()
                                        except Exception as ex:
                                            ui.notify(f"Error al cambiar estado: {ex}", type="negative")

                                    ui.button("Guardar", icon="check", on_click=cambiar_est).props("dense unelevated color=primary")

                filtro_tipo.on_value_change(renderizar_reportes)
                filtro_estado.on_value_change(renderizar_reportes)
                renderizar_reportes()

            # PANEL 2: Gestión Completa de Usuarios
            with ui.tab_panel(tab_usuarios).classes("p-0 pt-4 flex flex-col gap-4"):
                with ui.row().classes("w-full justify-between items-center mb-1"):
                    ui.label("Directorio Institucional y Control de Cuentas").classes("text-lg font-bold text-gray-800")
                    ui.label("Control de roles, accesos y credenciales").classes("text-xs text-gray-500")

                contenedor_usuarios = ui.column().classes("w-full gap-3")

                def renderizar_usuarios():
                    contenedor_usuarios.clear()
                    try:
                        with container.database.get_session() as s:
                            uc_listar = container.listar_usuarios_admin_use_case(s)
                            usuarios_lista = uc_listar.ejecutar(usuario_actual.id)
                    except Exception as ex:
                        with contenedor_usuarios:
                            ui.label(f"Error al cargar usuarios: {ex}").classes("text-red-500")
                        return

                    if not usuarios_lista:
                        with contenedor_usuarios:
                            with ui.card().classes("w-full p-8 text-center text-gray-400 bg-white border border-dashed rounded-xl"):
                                ui.label("No hay usuarios registrados.").classes("font-medium")
                        return

                    with contenedor_usuarios:
                        for u in usuarios_lista:
                            es_propio_admin = (u.id == usuario_actual.id)

                            with ui.card().classes(
                                "w-full p-4 rounded-xl bg-white shadow-sm border border-gray-100 "
                                "flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
                            ):
                                # Información del usuario
                                with ui.row().classes("items-center gap-3 flex-grow"):
                                    avatar_icon = "security" if u.es_admin else "person"
                                    avatar_bg = "bg-purple-100 text-purple-700" if u.es_admin else "bg-blue-100 text-blue-700"
                                    with ui.avatar().classes(f"{avatar_bg} font-bold"):
                                        ui.icon(avatar_icon)

                                    with ui.column().classes("gap-0.5"):
                                        with ui.row().classes("items-center gap-2 flex-wrap"):
                                            ui.label(u.nombre).classes("font-bold text-gray-800 text-base")
                                            if es_propio_admin:
                                                ui.badge("Tú / Sesión actual", color="indigo").props("dense text-xs")

                                            # Badge de rol
                                            if u.es_admin:
                                                ui.badge("ADMIN", color="deep-purple").props("rounded text-xs")
                                            else:
                                                ui.badge("USUARIO", color="blue-grey").props("outline text-xs")

                                            # Badge de estado
                                            if u.activo:
                                                ui.badge("Activo", color="positive").props("dense text-xs")
                                            else:
                                                ui.badge("Bloqueado", color="negative").props("dense text-xs")

                                        ui.label(u.email).classes("text-xs text-gray-600 font-mono")
                                        if u.fecha_registro:
                                            ui.label(f"Registrado el: {u.fecha_registro[:10]}").classes("text-xs text-gray-400")

                                # Barra de acciones
                                with ui.row().classes("items-center gap-2 flex-wrap shrink-0"):

                                    # 1. Botón Cambiar Clave
                                    def abrir_dialog_clave(target_u=u):
                                        with ui.dialog() as dlg_clave, ui.card().classes("p-6 w-96 rounded-2xl gap-4"):
                                            ui.label(f"Cambiar Contraseña: {target_u.nombre}").classes("text-base font-bold text-gray-800")
                                            input_nueva_clave = ui.input(
                                                label="Nueva Contraseña (mínimo 6 caracteres) *",
                                                password=True,
                                                password_toggle_button=True,
                                            ).props("outlined dense").classes("w-full")

                                            input_confirm_clave = ui.input(
                                                label="Confirmar Contraseña *",
                                                password=True,
                                                password_toggle_button=True,
                                            ).props("outlined dense").classes("w-full")

                                            def ejecutar_cambio_clave():
                                                c1 = (input_nueva_clave.value or "").strip()
                                                c2 = (input_confirm_clave.value or "").strip()
                                                if not c1 or len(c1) < 6:
                                                    ui.notify("La contraseña debe tener al menos 6 caracteres.", type="negative")
                                                    return
                                                if c1 != c2:
                                                    ui.notify("Las contraseñas no coinciden.", type="negative")
                                                    return

                                                try:
                                                    with container.database.get_session() as ses:
                                                        uc = container.restablecer_contrasena_usuario_use_case(ses)
                                                        uc.ejecutar(
                                                            usuario_id=target_u.id,
                                                            nueva_contrasena=c1,
                                                            admin_id=usuario_actual.id,
                                                        )
                                                    dlg_clave.close()
                                                    ui.notify(f"Contraseña de '{target_u.nombre}' actualizada exitosamente.", type="positive")
                                                except Exception as ex:
                                                    ui.notify(f"Error: {ex}", type="negative")

                                            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                                                ui.button("Cancelar", on_click=dlg_clave.close).props("flat")
                                                ui.button("Guardar Contraseña", icon="lock_reset", on_click=ejecutar_cambio_clave).props(
                                                    "unelevated color=primary"
                                                )
                                        dlg_clave.open()

                                    ui.button(
                                        "Clave",
                                        icon="key",
                                        on_click=abrir_dialog_clave,
                                    ).props("dense outline color=primary size=sm").tooltip("Restablecer contraseña del usuario")

                                    # 2. Botón Cambiar Rol (Ascender / Degradar)
                                    nuevo_rol_sugerido = "usuario" if u.es_admin else "admin"
                                    accion_rol_label = "Hacer Usuario" if u.es_admin else "Ascender a Admin"
                                    btn_rol_color = "warning" if u.es_admin else "secondary"

                                    def abrir_dialog_rol(target_u=u, n_rol=nuevo_rol_sugerido):
                                        with ui.dialog() as dlg_rol, ui.card().classes("p-6 w-96 rounded-2xl gap-4"):
                                            ui.icon("manage_accounts", size="lg").classes("text-amber-600 mx-auto")
                                            ui.label("Confirmar Cambio de Rol").classes("text-base font-bold text-gray-800 text-center")
                                            ui.label(
                                                f"¿Deseas cambiar el rol de '{target_u.nombre}' a '{n_rol.upper()}'?"
                                            ).classes("text-sm text-gray-600 text-center")

                                            def ejecutar_cambio_rol():
                                                try:
                                                    with container.database.get_session() as ses:
                                                        uc = container.cambiar_rol_usuario_use_case(ses)
                                                        uc.ejecutar(
                                                            admin_id=usuario_actual.id,
                                                            usuario_id=target_u.id,
                                                            nuevo_rol=n_rol,
                                                        )
                                                    dlg_rol.close()
                                                    ui.notify(f"Rol de '{target_u.nombre}' cambiado a {n_rol.upper()}.", type="positive")
                                                    renderizar_usuarios()
                                                except Exception as ex:
                                                    ui.notify(f"Error: {ex}", type="negative")

                                            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                                                ui.button("Cancelar", on_click=dlg_rol.close).props("flat")
                                                ui.button("Confirmar", icon="check", on_click=ejecutar_cambio_rol).props(
                                                    f"unelevated color={btn_rol_color}"
                                                )
                                        dlg_rol.open()

                                    btn_rol = ui.button(
                                        accion_rol_label,
                                        icon="manage_accounts",
                                        on_click=abrir_dialog_rol,
                                    ).props(f"dense outline color={btn_rol_color} size=sm")
                                    if es_propio_admin:
                                        btn_rol.props(add="disable")
                                        btn_rol.tooltip("No puedes degradar tu propia cuenta")
                                    else:
                                        btn_rol.tooltip(f"Cambiar rol a {nuevo_rol_sugerido.upper()}")

                                    # 3. Botón Bloquear / Desbloquear
                                    nuevo_estado = not u.activo
                                    label_estado = "Desbloquear" if not u.activo else "Bloquear"
                                    icon_estado = "lock_open" if not u.activo else "block"
                                    color_estado = "positive" if not u.activo else "amber-9"

                                    def abrir_dialog_estado(target_u=u, act=nuevo_estado):
                                        accion_txt = "activar" if act else "bloquear temporalmente"
                                        with ui.dialog() as dlg_est, ui.card().classes("p-6 w-96 rounded-2xl gap-4"):
                                            ui.icon("block" if not act else "check_circle", size="lg").classes(
                                                "text-red-600 mx-auto" if not act else "text-green-600 mx-auto"
                                            )
                                            ui.label(f"¿Confirmas {accion_txt} a este usuario?").classes("text-base font-bold text-gray-800 text-center")
                                            ui.label(
                                                f"Usuario: {target_u.nombre} ({target_u.email})"
                                            ).classes("text-xs text-gray-500 text-center")

                                            def ejecutar_cambio_estado():
                                                try:
                                                    with container.database.get_session() as ses:
                                                        uc = container.cambiar_estado_usuario_use_case(ses)
                                                        uc.ejecutar(
                                                            admin_id=usuario_actual.id,
                                                            usuario_id=target_u.id,
                                                            activo=act,
                                                        )
                                                    dlg_est.close()
                                                    msg = "activada" if act else "bloqueada"
                                                    ui.notify(f"Cuenta de '{target_u.nombre}' {msg}.", type="positive")
                                                    renderizar_usuarios()
                                                except Exception as ex:
                                                    ui.notify(f"Error: {ex}", type="negative")

                                            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                                                ui.button("Cancelar", on_click=dlg_est.close).props("flat")
                                                ui.button("Aceptar", icon="check", on_click=ejecutar_cambio_estado).props(
                                                    f"unelevated color={color_estado}"
                                                )
                                        dlg_est.open()

                                    btn_estado = ui.button(
                                        label_estado,
                                        icon=icon_estado,
                                        on_click=abrir_dialog_estado,
                                    ).props(f"dense outline color={color_estado} size=sm")
                                    if es_propio_admin:
                                        btn_estado.props(add="disable")
                                        btn_estado.tooltip("No puedes bloquear tu propia cuenta")
                                    else:
                                        btn_estado.tooltip(f"{label_estado} acceso a la plataforma")

                                    # 4. Botón Eliminar
                                    def abrir_dialog_eliminar(target_u=u):
                                        with ui.dialog() as dlg_del, ui.card().classes("p-6 w-96 rounded-2xl gap-4 border border-red-200"):
                                            ui.icon("delete_forever", size="xl").classes("text-red-600 mx-auto")
                                            ui.label("¿Eliminar Usuario Definitivamente?").classes("text-base font-bold text-red-900 text-center")
                                            ui.label(
                                                f"Se eliminará la cuenta de '{target_u.nombre}' ({target_u.email}) y todos sus reportes asociados en cascada. Esta acción NO se puede deshacer."
                                            ).classes("text-xs text-gray-600 text-center")

                                            def ejecutar_eliminacion():
                                                try:
                                                    with container.database.get_session() as ses:
                                                        uc = container.eliminar_usuario_use_case(ses)
                                                        uc.ejecutar(
                                                            admin_id=usuario_actual.id,
                                                            usuario_id=target_u.id,
                                                        )
                                                    dlg_del.close()
                                                    ui.notify(f"Usuario '{target_u.nombre}' eliminado permanentemente.", type="positive")
                                                    renderizar_usuarios()
                                                    # Actualizar contador
                                                    with container.database.get_session() as ses:
                                                        st = container.gestionar_reporte_admin_use_case(ses).obtener_estadisticas_globales(usuario_actual.id)
                                                        lbl_total_users.set_text(str(st["total_usuarios"]))
                                                        lbl_total_rep.set_text(str(st["total_reportes"]))
                                                except Exception as ex:
                                                    ui.notify(f"Error: {ex}", type="negative")

                                            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                                                ui.button("Cancelar", on_click=dlg_del.close).props("flat")
                                                ui.button("Eliminar Permanentemente", icon="delete", on_click=ejecutar_eliminacion).props(
                                                    "unelevated color=negative"
                                                )
                                        dlg_del.open()

                                    btn_del = ui.button(
                                        "Eliminar",
                                        icon="delete",
                                        on_click=abrir_dialog_eliminar,
                                    ).props("dense outline color=negative size=sm")
                                    if es_propio_admin:
                                        btn_del.props(add="disable")
                                        btn_del.tooltip("No puedes eliminar tu propia cuenta")
                                    else:
                                        btn_del.tooltip("Eliminar permanentemente este usuario")

                renderizar_usuarios()
