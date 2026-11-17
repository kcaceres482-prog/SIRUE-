"""Caso de uso: Registrar un reporte de objeto encontrado."""

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
from sirue.domain.exceptions.domain_exceptions import (
    FotoRequeridaError,
    UsuarioNoEncontradoError,
)
from sirue.domain.ports.coincidencia_repository import CoincidenciaRepository
from sirue.domain.ports.foto_storage import FotoStorage
from sirue.domain.ports.notificacion_service import NotificacionService
from sirue.domain.ports.reporte_repository import ReporteRepository
from sirue.domain.ports.usuario_repository import UsuarioRepository


class RegistrarObjetoEncontrado:
    """Caso de uso para registrar un reporte de objeto encontrado en el campus.

    Exige fotografía obligatoria y ubicación en el campus. Guarda la imagen
    en el almacenamiento local vía FotoStorage, persiste el reporte, busca
    coincidencias activas con reportes de objetos perdidos y dispara
    las notificaciones pertinentes.
    """

    def __init__(
        self,
        reporte_repo: ReporteRepository,
        usuario_repo: UsuarioRepository,
        foto_storage: FotoStorage,
        coincidencia_repo: CoincidenciaRepository,
        motor_coincidencias: MotorCoincidencias,
        notificacion_service: Optional[NotificacionService] = None,
    ) -> None:
        """Inicializa el caso de uso inyectando sus puertos y servicios.

        Args:
            reporte_repo: Puerto de persistencia de reportes.
            usuario_repo: Puerto de persistencia de usuarios.
            foto_storage: Puerto de almacenamiento físico de fotos.
            coincidencia_repo: Puerto de persistencia de coincidencias.
            motor_coincidencias: Servicio de afinidad y coincidencia.
            notificacion_service: Puerto de notificaciones (opcional).
        """
        self._reporte_repo = reporte_repo
        self._usuario_repo = usuario_repo
        self._foto_storage = foto_storage
        self._coincidencia_repo = coincidencia_repo
        self._motor_coincidencias = motor_coincidencias
        self._notificacion_service = notificacion_service

    def ejecutar(
        self, dto: ReporteInputDTO, umbral_coincidencia: float = 0.4
    ) -> tuple[ReporteOutputDTO, list[CoincidenciaOutputDTO]]:
        """Ejecuta el registro del hallazgo y detección de coincidencias.

        Args:
            dto: Datos de entrada que deben contener foto_bytes y coordenadas.
            umbral_coincidencia: Umbral de similitud (0.4 por defecto).

        Returns:
            Tupla (ReporteOutputDTO, lista de CoincidenciaOutputDTO generadas).

        Raises:
            UsuarioNoEncontradoError: Si el usuario no existe.
            FotoRequeridaError: Si no se adjuntan los bytes de la foto.
            ValidacionError: Si las coordenadas o datos son inválidos.
        """
        # 1. Validar que el usuario que reporta exista
        usuario = self._usuario_repo.obtener_por_id(dto.usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(
                f"El usuario con ID '{dto.usuario_id}' no está registrado."
            )

        # 2. Validar presencia de foto antes del almacenamiento
        if not dto.foto_bytes:
            raise FotoRequeridaError(
                "Es obligatorio adjuntar una fotografía para registrar un objeto encontrado."
            )

        # 3. Guardar fotografía física en el storage
        nombre_archivo = dto.foto_nombre or f"hallazgo_{uuid.uuid4().hex[:8]}.jpg"
        foto_ruta = self._foto_storage.guardar_foto(dto.foto_bytes, nombre_archivo)

        # 4. Creación validada mediante la Factory
        reporte = ReporteFactory.crear_reporte_encontrado(dto)
        reporte.foto_ruta = foto_ruta

        # 5. Persistir reporte en el repositorio
        reporte_guardado = self._reporte_repo.guardar(reporte)

        # 6. Búsqueda proactiva de coincidencias con reportes PERDIDOS activos
        perdidos_activos = self._reporte_repo.listar_activos_por_tipo(
            TipoReporte.PERDIDO
        )
        matches = self._motor_coincidencias.buscar_coincidencias(
            reporte_guardado, perdidos_activos, umbral=umbral_coincidencia
        )

        coincidencias_generadas: list[CoincidenciaOutputDTO] = []

        # 7. Registrar coincidencias y notificar
        for perdido, puntuacion, detalles in matches:
            if not self._coincidencia_repo.existe_coincidencia(
                perdido.id, reporte_guardado.id
            ):
                coincidencia = Coincidencia(
                    id=str(uuid.uuid4()),
                    reporte_perdido_id=perdido.id,
                    reporte_encontrado_id=reporte_guardado.id,
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
                        reporte_match=perdido,
                    )
                    usuario_perdedor = self._usuario_repo.obtener_por_id(
                        perdido.usuario_id
                    )
                    if usuario_perdedor:
                        self._notificacion_service.notificar_coincidencia(
                            usuario=usuario_perdedor,
                            coincidencia=coincidencia,
                            reporte_propio=perdido,
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
                        titulo_perdido=perdido.titulo,
                        titulo_encontrado=reporte_guardado.titulo,
                    )
                )

        # 8. Construir DTO de salida
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
