"""Caso de uso: Registrar un reporte de objeto perdido."""

from __future__ import annotations

import uuid
from typing import Optional

from sirue.application.dtos.reporte_dto import (
    CoincidenciaOutputDTO,
    ReporteInputDTO,
    ReporteOutputDTO,
)
from sirue.application.factories.reporte_factory import ReporteFactory
from sirue.application.services.motor_coincidencias import MotorCoincidencias
from sirue.domain.entities.coincidencia import Coincidencia
from sirue.domain.entities.reporte_objeto import TipoReporte
from sirue.domain.exceptions.domain_exceptions import UsuarioNoEncontradoError
from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.domain.ports.notificacion_service import NotificacionService
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.domain.ports.usuario_repository import UsuarioRepository


class RegistrarObjetoPerdido:
    """Caso de uso para registrar un reporte de objeto perdido.

    Orquesta la validación del usuario, la creación del reporte
    mediante ReporteFactory, su persistencia, la búsqueda proactiva
    de coincidencias con objetos encontrados activos y el despacho
    de notificaciones automáticas.
    """

    def __init__(
        self,
        reporte_repo: ReporteRepository,
        usuario_repo: UsuarioRepository,
        coincidencia_repo: CoincidenciaRepository,
        motor_coincidencias: MotorCoincidencias,
        notificacion_service: Optional[NotificacionService] = None,
    ) -> None:
        """Inicializa el caso de uso inyectando sus dependencias.

        Args:
            reporte_repo: Puerto de persistencia de reportes.
            usuario_repo: Puerto de persistencia de usuarios.
            coincidencia_repo: Puerto de persistencia de coincidencias.
            motor_coincidencias: Servicio de afinidad y coincidencia.
            notificacion_service: Puerto de notificaciones (opcional).
        """
        self._reporte_repo = reporte_repo
        self._usuario_repo = usuario_repo
        self._coincidencia_repo = coincidencia_repo
        self._motor_coincidencias = motor_coincidencias
        self._notificacion_service = notificacion_service

    def ejecutar(
        self, dto: ReporteInputDTO, umbral_coincidencia: float = 0.4
    ) -> tuple[ReporteOutputDTO, list[CoincidenciaOutputDTO]]:
        """Ejecuta el registro del objeto perdido y el procesamiento de afinidad.

        Args:
            dto: Datos de entrada del reporte.
            umbral_coincidencia: Umbral mínimo para generar coincidencia (0.4 por defecto).

        Returns:
            Tupla (ReporteOutputDTO, lista de CoincidenciaOutputDTO generadas).

        Raises:
            UsuarioNoEncontradoError: Si el usuario que reporta no existe.
            ValidacionError: Si los datos del reporte son inconsistentes.
            DescripcionInsuficienteError: Si la descripción no alcanza 20 caracteres.
        """
        # 1. Validar que el usuario que reporta exista
        usuario = self._usuario_repo.obtener_por_id(dto.usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(
                f"El usuario con ID '{dto.usuario_id}' no está registrado."
            )

        # 2. Instanciación validada a través de la Factory
        reporte = ReporteFactory.crear_reporte_perdido(dto)

        # 3. Persistir reporte en el repositorio
        reporte_guardado = self._reporte_repo.guardar(reporte)

        # 4. Búsqueda proactiva de coincidencias con reportes ENCONTRADOS activos
        encontrados_activos = self._reporte_repo.listar_activos_por_tipo(
            TipoReporte.ENCONTRADO
        )
        matches = self._motor_coincidencias.buscar_coincidencias(
            reporte_guardado, encontrados_activos, umbral=umbral_coincidencia
        )

        coincidencias_generadas: list[CoincidenciaOutputDTO] = []

        # 5. Registrar coincidencias y notificar
        for encontrado, puntuacion, detalles in matches:
            # Evitar registrar duplicados si ya existiera la coincidencia
            if not self._coincidencia_repo.existe_coincidencia(
                reporte_guardado.id, encontrado.id
            ):
                coincidencia = Coincidencia(
                    id=str(uuid.uuid4()),
                    reporte_perdido_id=reporte_guardado.id,
                    reporte_encontrado_id=encontrado.id,
                    puntuacion=puntuacion,
                    detalles=detalles,
                )
                self._coincidencia_repo.guardar(coincidencia)

                # Notificar a ambas partes si el servicio está configurado
                if self._notificacion_service:
                    self._notificacion_service.notificar_coincidencia(
                        usuario=usuario,
                        coincidencia=coincidencia,
                        reporte_propio=reporte_guardado,
                        reporte_match=encontrado,
                    )
                    usuario_encontrador = self._usuario_repo.obtener_por_id(
                        encontrado.usuario_id
                    )
                    if usuario_encontrador:
                        self._notificacion_service.notificar_coincidencia(
                            usuario=usuario_encontrador,
                            coincidencia=coincidencia,
                            reporte_propio=encontrado,
                            reporte_match=reporte_guardado,
                        )

                coincidencias_generadas.append(
                    CoincidenciaOutputDTO(
                        id=coincidencia.id,
                        reporte_perdido_id=coincidencia.reporte_perdido_id,
                        reporte_encontrado_id=coincidencia.reporte_encontrado_id,
                        puntuacion=coincidencia.puntuacion,
                        estado=coincidencia.estado.value,
                        fecha_deteccion=coincidencia.fecha_deteccion.isoformat(),
                        detalles=coincidencia.detalles,
                        titulo_perdido=reporte_guardado.titulo,
                        titulo_encontrado=encontrado.titulo,
                    )
                )

        # 6. Construir DTO de salida
        output_dto = ReporteOutputDTO(
            id=reporte_guardado.id,
            tipo=reporte_guardado.tipo.value,
            titulo=reporte_guardado.titulo,
            descripcion=reporte_guardado.descripcion,
            categoria=reporte_guardado.categoria.value,
            referencia=reporte_guardado.ubicacion.referencia_interna,
            fecha_hora_incidente=reporte_guardado.fecha_hora_incidente.valor.isoformat(),
            usuario_id=reporte_guardado.usuario_id,
            nombre_usuario=usuario.nombre,
            foto_ruta=reporte_guardado.foto_ruta,
            palabras_clave=reporte_guardado.palabras_clave,
            estado=reporte_guardado.estado.value,
            fecha_creacion=reporte_guardado.fecha_creacion.isoformat(),
        )

        return output_dto, coincidencias_generadas
