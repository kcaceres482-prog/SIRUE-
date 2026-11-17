"""Caso de uso: Procesar coincidencias, confirmación, descarte y notificaciones."""

from __future__ import annotations

import uuid
from typing import Optional

from sirue.application.dtos.reporte_dto import CoincidenciaOutputDTO
from sirue.application.services.motor_coincidencias import MotorCoincidencias
from sirue.domain.entities.coincidencia import Coincidencia
from sirue.domain.entities.reporte_objeto import TipoReporte
from sirue.domain.exceptions.domain_exceptions import (
    CoincidenciaNoEncontradaError,
    ReporteNoEncontradoError,
)
from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.domain.ports.notificacion_service import NotificacionService
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.domain.ports.usuario_repository import UsuarioRepository


class ProcesarCoincidenciasYNotificar:
    """Caso de uso para gestionar el ciclo de vida de las coincidencias.

    Permite a los usuarios confirmar que un hallazgo corresponde a su pertenencia
    (resolviendo ambos reportes), descartar falsos positivos, listar coincidencias
    y ejecutar el reprocesamiento por lotes de reportes activos.
    """

    def __init__(
        self,
        coincidencia_repo: CoincidenciaRepository,
        reporte_repo: ReporteRepository,
        usuario_repo: UsuarioRepository,
        motor_coincidencias: Optional[MotorCoincidencias] = None,
        notificacion_service: Optional[NotificacionService] = None,
    ) -> None:
        """Inicializa el caso de uso con sus dependencias inyectadas.

        Args:
            coincidencia_repo: Puerto de persistencia de coincidencias.
            reporte_repo: Puerto de persistencia de reportes.
            usuario_repo: Puerto de persistencia de usuarios.
            motor_coincidencias: Motor de afinidad para reprocesamientos en lote.
            notificacion_service: Servicio para despachar notificaciones.
        """
        self._coincidencia_repo = coincidencia_repo
        self._reporte_repo = reporte_repo
        self._usuario_repo = usuario_repo
        self._motor_coincidencias = motor_coincidencias or MotorCoincidencias()
        self._notificacion_service = notificacion_service

    def confirmar_coincidencia(self, coincidencia_id: str) -> CoincidenciaOutputDTO:
        """Confirma una coincidencia, marcando ambos reportes asociados como RESUELTOS.

        Args:
            coincidencia_id: UUID de la coincidencia a confirmar.

        Returns:
            CoincidenciaOutputDTO con el estado actualizado.

        Raises:
            CoincidenciaNoEncontradaError: Si la coincidencia no existe.
            ReporteNoEncontradoError: Si alguno de los reportes asociados no se encuentra.
        """
        coincidencia = self._coincidencia_repo.obtener_por_id(coincidencia_id)
        if not coincidencia:
            raise CoincidenciaNoEncontradaError(
                f"No existe coincidencia con ID '{coincidencia_id}'."
            )

        # 1. Cambiar estado de la entidad Coincidencia
        coincidencia.confirmar()
        self._coincidencia_repo.actualizar(coincidencia)

        # 2. Marcar ambos reportes como resueltos
        reporte_perdido = self._reporte_repo.obtener_por_id(
            coincidencia.reporte_perdido_id
        )
        reporte_encontrado = self._reporte_repo.obtener_por_id(
            coincidencia.reporte_encontrado_id
        )

        if not reporte_perdido or not reporte_encontrado:
            raise ReporteNoEncontradoError(
                "No se encontraron uno o ambos reportes asociados a la coincidencia."
            )

        reporte_perdido.marcar_resuelto()
        reporte_encontrado.marcar_resuelto()

        self._reporte_repo.actualizar(reporte_perdido)
        self._reporte_repo.actualizar(reporte_encontrado)

        return CoincidenciaOutputDTO(
            id=coincidencia.id,
            reporte_perdido_id=coincidencia.reporte_perdido_id,
            reporte_encontrado_id=coincidencia.reporte_encontrado_id,
            puntuacion=coincidencia.puntuacion,
            estado=coincidencia.estado.value,
            fecha_deteccion=coincidencia.fecha_deteccion.isoformat(),
            detalles=coincidencia.detalles,
            titulo_perdido=reporte_perdido.titulo,
            titulo_encontrado=reporte_encontrado.titulo,
        )

    def descartar_coincidencia(self, coincidencia_id: str) -> CoincidenciaOutputDTO:
        """Descarta una coincidencia marcada como falso positivo.

        Args:
            coincidencia_id: UUID de la coincidencia a descartar.

        Returns:
            CoincidenciaOutputDTO con estado DESCARTADA.

        Raises:
            CoincidenciaNoEncontradaError: Si la coincidencia no existe.
        """
        coincidencia = self._coincidencia_repo.obtener_por_id(coincidencia_id)
        if not coincidencia:
            raise CoincidenciaNoEncontradaError(
                f"No existe coincidencia con ID '{coincidencia_id}'."
            )

        coincidencia.descartar()
        self._coincidencia_repo.actualizar(coincidencia)

        # Obtener títulos descriptivos si existen
        p = self._reporte_repo.obtener_por_id(coincidencia.reporte_perdido_id)
        e = self._reporte_repo.obtener_por_id(coincidencia.reporte_encontrado_id)

        return CoincidenciaOutputDTO(
            id=coincidencia.id,
            reporte_perdido_id=coincidencia.reporte_perdido_id,
            reporte_encontrado_id=coincidencia.reporte_encontrado_id,
            puntuacion=coincidencia.puntuacion,
            estado=coincidencia.estado.value,
            fecha_deteccion=coincidencia.fecha_deteccion.isoformat(),
            detalles=coincidencia.detalles,
            titulo_perdido=p.titulo if p else "",
            titulo_encontrado=e.titulo if e else "",
        )

    def obtener_coincidencias_por_usuario(
        self, usuario_id: str
    ) -> list[CoincidenciaOutputDTO]:
        """Obtiene todas las coincidencias relacionadas con los reportes de un usuario.

        Args:
            usuario_id: UUID del usuario.

        Returns:
            Lista de CoincidenciaOutputDTO ordenadas por afinidad descendente.
        """
        reportes_usuario = self._reporte_repo.listar_por_usuario(usuario_id)
        coincidencias_vistas: dict[str, Coincidencia] = {}

        for rep in reportes_usuario:
            matches = self._coincidencia_repo.listar_por_reporte(rep.id)
            for m in matches:
                if m.id not in coincidencias_vistas:
                    coincidencias_vistas[m.id] = m

        resultado: list[CoincidenciaOutputDTO] = []
        for c in coincidencias_vistas.values():
            p = self._reporte_repo.obtener_por_id(c.reporte_perdido_id)
            e = self._reporte_repo.obtener_por_id(c.reporte_encontrado_id)
            resultado.append(
                CoincidenciaOutputDTO(
                    id=c.id,
                    reporte_perdido_id=c.reporte_perdido_id,
                    reporte_encontrado_id=c.reporte_encontrado_id,
                    puntuacion=c.puntuacion,
                    estado=c.estado.value,
                    fecha_deteccion=c.fecha_deteccion.isoformat(),
                    detalles=c.detalles,
                    titulo_perdido=p.titulo if p else "",
                    titulo_encontrado=e.titulo if e else "",
                )
            )

        resultado.sort(key=lambda x: x.puntuacion, reverse=True)
        return resultado

    def reprocesar_coincidencias(
        self, umbral: float = 0.4
    ) -> list[CoincidenciaOutputDTO]:
        """Reprocesa por lotes todos los reportes activos para descubrir nuevas coincidencias.

        Args:
            umbral: Puntuación mínima de afinidad.

        Returns:
            Lista de nuevas coincidencias generadas.
        """
        perdidos_activos = self._reporte_repo.listar_activos_por_tipo(
            TipoReporte.PERDIDO
        )
        encontrados_activos = self._reporte_repo.listar_activos_por_tipo(
            TipoReporte.ENCONTRADO
        )

        nuevas_coincidencias: list[CoincidenciaOutputDTO] = []

        for perdido in perdidos_activos:
            matches = self._motor_coincidencias.buscar_coincidencias(
                perdido, encontrados_activos, umbral=umbral
            )
            for encontrado, puntuacion, detalles in matches:
                if not self._coincidencia_repo.existe_coincidencia(
                    perdido.id, encontrado.id
                ):
                    coincidencia = Coincidencia(
                        id=str(uuid.uuid4()),
                        reporte_perdido_id=perdido.id,
                        reporte_encontrado_id=encontrado.id,
                        puntuacion=puntuacion,
                        detalles=detalles,
                    )
                    self._coincidencia_repo.guardar(coincidencia)

                    # Despachar notificaciones
                    if self._notificacion_service:
                        u_perdedor = self._usuario_repo.obtener_por_id(perdido.usuario_id)
                        u_encontrador = self._usuario_repo.obtener_por_id(
                            encontrado.usuario_id
                        )
                        if u_perdedor:
                            self._notificacion_service.notificar_coincidencia(
                                u_perdedor, coincidencia, perdido, encontrado
                            )
                        if u_encontrador:
                            self._notificacion_service.notificar_coincidencia(
                                u_encontrador, coincidencia, encontrado, perdido
                            )

                    nuevas_coincidencias.append(
                        CoincidenciaOutputDTO(
                            id=coincidencia.id,
                            reporte_perdido_id=coincidencia.reporte_perdido_id,
                            reporte_encontrado_id=coincidencia.reporte_encontrado_id,
                            puntuacion=coincidencia.puntuacion,
                            estado=coincidencia.estado.value,
                            fecha_deteccion=coincidencia.fecha_deteccion.isoformat(),
                            detalles=coincidencia.detalles,
                            titulo_perdido=perdido.titulo,
                            titulo_encontrado=encontrado.titulo,
                        )
                    )

        return nuevas_coincidencias
