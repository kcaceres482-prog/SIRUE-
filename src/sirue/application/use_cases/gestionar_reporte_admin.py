"""Caso de uso: Supervisión, gestión de estados y control administrativo del campus."""

from __future__ import annotations

from typing import Any, Optional

from sirue.application.dtos.reporte_dto import ReporteOutputDTO
from sirue.domain.entities.reporte_objeto import EstadoReporte, TipoReporte
from sirue.domain.exceptions.domain_exceptions import (
    AccesoDenegadoError,
    ReporteNoEncontradoError,
    UsuarioNoEncontradoError,
    ValidacionError,
)
from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.domain.ports.notificacion_service import NotificacionService
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.domain.ports.usuario_repository import UsuarioRepository


class GestionarReporteAdmin:
    """Caso de uso reservado para usuarios con rol 'admin'.

    Permite auditar todos los reportes del campus, cambiar su estado
    administrativo (Activo, En proceso, Recuperado, Cerrado) y acceder
    a estadísticas globales de la comunidad.
    """

    def __init__(
        self,
        reporte_repo: ReporteRepository,
        usuario_repo: UsuarioRepository,
        coincidencia_repo: CoincidenciaRepository,
        notificacion_service: Optional[NotificacionService] = None,
    ) -> None:
        self._reporte_repo = reporte_repo
        self._usuario_repo = usuario_repo
        self._coincidencia_repo = coincidencia_repo
        self._notificacion_service = notificacion_service

    def _verificar_admin(self, admin_user_id: str) -> None:
        usuario = self._usuario_repo.obtener_por_id(admin_user_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario '{admin_user_id}' no encontrado.")
        if not usuario.es_admin():
            raise AccesoDenegadoError("Acceso denegado: se requieren privilegios de Administrador.")

    def cambiar_estado_reporte(
        self,
        reporte_id: str,
        nuevo_estado_str: str,
        admin_user_id: str,
    ) -> ReporteOutputDTO:
        """Modifica el estado administrativo de un reporte en el campus."""
        self._verificar_admin(admin_user_id)

        try:
            nuevo_estado = EstadoReporte(nuevo_estado_str.upper().strip())
        except ValueError:
            validos = [e.value for e in EstadoReporte]
            raise ValidacionError(f"Estado inválido: '{nuevo_estado_str}'. Válidos: {validos}")

        reporte = self._reporte_repo.obtener_por_id(reporte_id)
        if not reporte:
            raise ReporteNoEncontradoError(f"No existe reporte con ID '{reporte_id}'.")

        estado_anterior = reporte.estado.value
        reporte.cambiar_estado(nuevo_estado)
        self._reporte_repo.actualizar(reporte)

        usuario_dueno = self._usuario_repo.obtener_por_id(reporte.usuario_id)

        # Notificar al dueño si el servicio de notificaciones está presente
        if self._notificacion_service and usuario_dueno and hasattr(self._notificacion_service, "_notificaciones"):
            mensaje = (
                f"El estado de tu reporte '{reporte.titulo}' ha sido actualizado "
                f"de {estado_anterior} a {nuevo_estado.value} por la administración del campus."
            )
            # Registrar notificación interna
            self._notificacion_service._notificaciones.append({
                "usuario_id": usuario_dueno.id,
                "mensaje": mensaje,
                "coincidencia_id": None,
                "fecha": reporte.fecha_creacion.isoformat(),
                "leido": False,
            })

        nombre_u = usuario_dueno.nombre if usuario_dueno else "Desconocido"

        return ReporteOutputDTO(
            id=reporte.id,
            tipo=reporte.tipo.value,
            titulo=reporte.titulo,
            descripcion=reporte.descripcion,
            categoria=reporte.categoria.value,
            referencia=reporte.ubicacion.referencia_interna,
            fecha_hora_incidente=reporte.fecha_hora_incidente.valor.isoformat(),
            usuario_id=reporte.usuario_id,
            nombre_usuario=nombre_u,
            foto_ruta=reporte.foto_ruta,
            palabras_clave=reporte.palabras_clave,
            estado=reporte.estado.value,
            fecha_creacion=reporte.fecha_creacion.isoformat(),
        )

    def listar_reportes_supervision(
        self,
        admin_user_id: str,
        tipo_filtro: Optional[str] = None,
        estado_filtro: Optional[str] = None,
    ) -> list[ReporteOutputDTO]:
        """Lista todos los reportes del campus con filtros opcionales."""
        self._verificar_admin(admin_user_id)

        todos = self._reporte_repo.listar_todos()
        resultado: list[ReporteOutputDTO] = []

        for r in todos:
            if tipo_filtro and r.tipo.value != tipo_filtro.upper():
                continue
            if estado_filtro and r.estado.value != estado_filtro.upper():
                continue

            usr = self._usuario_repo.obtener_por_id(r.usuario_id)
            resultado.append(
                ReporteOutputDTO(
                    id=r.id,
                    tipo=r.tipo.value,
                    titulo=r.titulo,
                    descripcion=r.descripcion,
                    categoria=r.categoria.value,
                    referencia=r.ubicacion.referencia_interna,
                    fecha_hora_incidente=r.fecha_hora_incidente.valor.isoformat(),
                    usuario_id=r.usuario_id,
                    nombre_usuario=usr.nombre if usr else "Estudiante",
                    foto_ruta=r.foto_ruta,
                    palabras_clave=r.palabras_clave,
                    estado=r.estado.value,
                    fecha_creacion=r.fecha_creacion.isoformat(),
                )
            )

        resultado.sort(key=lambda x: x.fecha_creacion, reverse=True)
        return resultado

    def obtener_estadisticas_globales(self, admin_user_id: str) -> dict[str, Any]:
        """Calcula métricas clave para el panel administrativo."""
        self._verificar_admin(admin_user_id)

        reportes = self._reporte_repo.listar_todos()
        usuarios = self._usuario_repo.listar_todos()
        coincidencias = self._coincidencia_repo.listar_pendientes()

        conteo_estados = {
            "ACTIVO": 0,
            "EN_PROCESO": 0,
            "RECUPERADO": 0,
            "CERRADO": 0,
            "RESUELTO": 0,
        }
        conteo_tipos = {"PERDIDO": 0, "ENCONTRADO": 0}

        for r in reportes:
            conteo_estados[r.estado.value] = conteo_estados.get(r.estado.value, 0) + 1
            conteo_tipos[r.tipo.value] = conteo_tipos.get(r.tipo.value, 0) + 1

        conteo_roles = {"admin": 0, "usuario": 0}
        for u in usuarios:
            conteo_roles[u.rol.value] = conteo_roles.get(u.rol.value, 0) + 1

        return {
            "total_reportes": len(reportes),
            "total_usuarios": len(usuarios),
            "coincidencias_pendientes": len(coincidencias),
            "perdidos": conteo_tipos["PERDIDO"],
            "encontrados": conteo_tipos["ENCONTRADO"],
            "activos": conteo_estados["ACTIVO"],
            "en_proceso": conteo_estados["EN_PROCESO"],
            "recuperados": conteo_estados["RECUPERADO"] + conteo_estados["RESUELTO"],
            "cerrados": conteo_estados["CERRADO"],
            "usuarios_admin": conteo_roles["admin"],
            "usuarios_estudiantes": conteo_roles["usuario"],
        }

    def listar_usuarios_control(self, admin_user_id: str) -> list[dict[str, Any]]:
        """Lista el directorio de usuarios registrados con conteo de reportes."""
        self._verificar_admin(admin_user_id)

        usuarios = self._usuario_repo.listar_todos()
        resultado = []

        for u in usuarios:
            reps = self._reporte_repo.listar_por_usuario(u.id)
            resultado.append({
                "id": u.id,
                "nombre": u.nombre,
                "email": u.email,
                "telefono": u.telefono or "No registrado",
                "rol": u.rol.value,
                "fecha_registro": u.fecha_registro.strftime("%Y-%m-%d"),
                "total_reportes": len(reps),
            })

        return resultado
