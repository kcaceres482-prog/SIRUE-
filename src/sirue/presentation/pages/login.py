"""Página de inicio de sesión y registro de usuarios institucionales UAB para SIRUE."""

from __future__ import annotations

from nicegui import ui

from sirue.application.dtos.usuario_dto import LoginInputDTO, RegistroUsuarioInputDTO
from sirue.domain.exceptions.domain_exceptions import (
    AccesoDenegadoError,
    CredencialesInvalidasError,
    CuentaBloqueadaError,
    EmailYaRegistradoError,
    ValidacionError,
)
from sirue.domain.value_objects.email_institucional import (
    DOMINIO_INSTITUCIONAL,
    es_email_institucional_valido,
)
from sirue.infrastructure.container import Container
from sirue.presentation.auth_session import iniciar_sesion
from sirue.presentation.components.header import crear_header


def crear_pagina_login(container: Container) -> None:
    """Construye la vista de autenticación y registro de nuevos usuarios de la UAB."""
    crear_header(container, active_tab="")

    with ui.column().classes("w-full max-w-md mx-auto p-4 my-8 gap-4"):
        with ui.card().classes("w-full p-6 rounded-2xl bg-white shadow-xl border border-gray-100"):

            # Cabecera con identidad visual de la UAB y SIRUE
            with ui.column().classes("w-full items-center text-center gap-1 mb-4"):
                ui.icon("school", size="xl").classes("text-blue-900")
                ui.label("SIRUE").classes("text-3xl font-extrabold text-blue-950 tracking-wider")
                ui.label("Universidad Adventista de Bolivia").classes(
                    "text-xs font-semibold uppercase text-amber-700 tracking-wide"
                )
                ui.label("Sistema Digital de Objetos Perdidos y Encontrados").classes(
                    "text-[11px] text-gray-500 mt-1"
                )

            # Pestañas para alternar de forma limpia entre Iniciar Sesión y Registro
            with ui.tabs().classes("w-full text-blue-900") as tabs:
                tab_login = ui.tab("Iniciar Sesión", icon="login")
                tab_registro = ui.tab("Registrarse", icon="person_add")

            with ui.tab_panels(tabs, value=tab_login).classes("w-full mt-2"):

                # ============================================================
                # 1. PANTALLA / PANEL DE INICIO DE SESIÓN
                # ============================================================
                with ui.tab_panel(tab_login).classes("p-0 pt-4 flex flex-col gap-3"):
                    input_email = ui.input(
                        label="Correo Institucional",
                        placeholder="nombre_usuario@uab.edu.bo",
                        validation={
                            f"Debe terminar en @{DOMINIO_INSTITUCIONAL}": lambda v: not v
                            or str(v).strip().lower().endswith(f"@{DOMINIO_INSTITUCIONAL}")
                        },
                    ).props("outlined clearable").classes("w-full")

                    # Comentario obligatorio bajo el correo de login
                    ui.label("Inicia sesión con tu correo institucional UAB.").classes(
                        "text-xs text-blue-700 font-medium italic -mt-1 mb-1 px-1"
                    )

                    input_password = ui.input(
                        label="Contraseña",
                        password=True,
                        password_toggle_button=True,
                    ).props("outlined").classes("w-full")

                    def ejecutar_login() -> None:
                        email = (input_email.value or "").strip()
                        password = input_password.value or ""

                        if not email or not password:
                            ui.notify(
                                "Por favor, ingresa tu correo institucional y contraseña.",
                                type="warning",
                                position="top",
                            )
                            return

                        if not es_email_institucional_valido(email):
                            ui.notify(
                                f"Solo se permiten correos institucionales con dominio @{DOMINIO_INSTITUCIONAL}.",
                                type="negative",
                                position="top",
                            )
                            return

                        try:
                            with container.database.get_session() as session:
                                uc = container.autenticar_usuario_use_case(session)
                                usuario = uc.ejecutar(
                                    LoginInputDTO(email=email, password=password)
                                )

                            # Persistir sesión autenticada en cookie cifrada
                            iniciar_sesion(usuario)

                            ui.notify(
                                f"¡Bienvenido(a), {usuario.nombre}!",
                                type="positive",
                                position="top",
                            )

                            # Redirección según rol institucional
                            if usuario.es_admin:
                                ui.navigate.to("/admin")
                            else:
                                ui.navigate.to("/")

                        except CuentaBloqueadaError as e:
                            ui.notify(str(e), type="negative", position="top", timeout=8000)
                        except (CredencialesInvalidasError, ValidacionError) as e:
                            ui.notify(str(e), type="negative", position="top")
                        except Exception as e:
                            ui.notify(
                                f"Error en la autenticación: {e}",
                                type="negative",
                                position="top",
                            )

                    ui.button(
                        "Iniciar Sesión",
                        icon="arrow_forward",
                        on_click=ejecutar_login,
                    ).props("unelevated color=primary size=md").classes("w-full py-2.5 font-bold shadow-md mt-2")

                    # Opción para ir al registro de usuario
                    with ui.row().classes("w-full justify-center items-center mt-3 pt-2 border-t border-gray-100"):
                        ui.label("¿Aún no tienes cuenta?").classes("text-xs text-gray-500")
                        ui.button(
                            "Regístrate aquí",
                            on_click=lambda: tabs.set_value(tab_registro),
                        ).props("flat dense color=primary text-xs font-bold")

                # ============================================================
                # 2. PANTALLA / PANEL DE REGISTRO
                # ============================================================
                with ui.tab_panel(tab_registro).classes("p-0 pt-4 flex flex-col gap-3"):
                    reg_nombre = ui.input(
                        label="Nombre Completo *",
                        placeholder="Ej: Daniel Ramos",
                    ).props("outlined clearable").classes("w-full")

                    reg_email = ui.input(
                        label="Correo Institucional *",
                        placeholder="usuario@uab.edu.bo",
                        validation={
                            f"Debe terminar en @{DOMINIO_INSTITUCIONAL}": lambda v: not v
                            or str(v).strip().lower().endswith(f"@{DOMINIO_INSTITUCIONAL}")
                        },
                    ).props("outlined clearable").classes("w-full")

                    # Comentario obligatorio bajo el correo de registro
                    ui.label(
                        "Regístrate utilizando tu correo institucional de la Universidad Adventista de Bolivia."
                    ).classes("text-xs text-blue-700 font-medium italic -mt-1 mb-1 px-1 leading-snug")

                    reg_telefono = ui.input(
                        label="Número de celular / WhatsApp *",
                        placeholder="Ej: 71234567 o +591 71234567",
                    ).props("outlined clearable").classes("w-full")

                    ui.label(
                        "Tu número permitirá que te contacten directamente si encuentran o reclaman tu pertenencia."
                    ).classes("text-xs text-gray-500 italic -mt-1 mb-1 px-1 leading-snug")

                    reg_password = ui.input(
                        label="Contraseña *",
                        placeholder="Mínimo 6 caracteres",
                        password=True,
                        password_toggle_button=True,
                    ).props("outlined").classes("w-full")

                    reg_confirm = ui.input(
                        label="Confirmar Contraseña *",
                        placeholder="Repite tu contraseña",
                        password=True,
                        password_toggle_button=True,
                        validation={
                            "Las contraseñas deben coincidir": lambda v: not v
                            or v == reg_password.value
                        },
                    ).props("outlined").classes("w-full")

                    def ejecutar_registro() -> None:
                        nombre = (reg_nombre.value or "").strip()
                        email = (reg_email.value or "").strip()
                        telefono = (reg_telefono.value or "").strip()
                        password = reg_password.value or ""
                        confirm = reg_confirm.value or ""

                        # Validaciones iniciales del frontend
                        if not nombre:
                            ui.notify("Por favor, ingresa tu nombre completo.", type="warning", position="top")
                            return

                        if not email:
                            ui.notify("Por favor, ingresa tu correo institucional.", type="warning", position="top")
                            return

                        if not es_email_institucional_valido(email):
                            ui.notify(
                                f"El correo debe pertenecer al dominio institucional @{DOMINIO_INSTITUCIONAL}.",
                                type="negative",
                                position="top",
                            )
                            return

                        if not telefono:
                            ui.notify("Por favor, ingresa tu número de celular o WhatsApp.", type="warning", position="top")
                            return

                        if not password:
                            ui.notify("Por favor, ingresa una contraseña segura.", type="warning", position="top")
                            return

                        if len(password) < 6:
                            ui.notify("La contraseña debe tener al menos 6 caracteres.", type="warning", position="top")
                            return

                        if password != confirm:
                            ui.notify("Las contraseñas no coinciden. Verifícalas.", type="negative", position="top")
                            return

                        try:
                            with container.database.get_session() as session:
                                uc = container.registrar_usuario_use_case(session)
                                dto = RegistroUsuarioInputDTO(
                                    nombre=nombre,
                                    email=email,
                                    password=password,
                                    confirm_password=confirm,
                                    telefono=telefono,
                                    rol="usuario",  # Rol obligatorio por defecto
                                )
                                nuevo_usuario = uc.ejecutar(dto, es_registro_publico=True)

                            # Persistir sesión del nuevo usuario
                            iniciar_sesion(nuevo_usuario)

                            ui.notify(
                                f"¡Registro exitoso! Bienvenido(a) a SIRUE, {nuevo_usuario.nombre}.",
                                type="positive",
                                position="top",
                            )

                            # Redirigir a la zona de reportes
                            ui.navigate.to("/")

                        except (EmailYaRegistradoError, ValidacionError, AccesoDenegadoError) as e:
                            ui.notify(str(e), type="negative", position="top")
                        except Exception as e:
                            ui.notify(f"Error al registrar cuenta: {e}", type="negative", position="top")

                    ui.button(
                        "Crear Cuenta Institucional",
                        icon="person_add",
                        on_click=ejecutar_registro,
                    ).props("unelevated color=positive size=md").classes("w-full py-2.5 font-bold shadow-md mt-2")

                    # Opción para regresar al Login
                    with ui.row().classes("w-full justify-center items-center mt-3 pt-2 border-t border-gray-100"):
                        ui.label("¿Ya tienes una cuenta institucional?").classes("text-xs text-gray-500")
                        ui.button(
                            "Inicia sesión aquí",
                            on_click=lambda: tabs.set_value(tab_login),
                        ).props("flat dense color=primary text-xs font-bold")
