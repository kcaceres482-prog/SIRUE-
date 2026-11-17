"""Servicio de notificaciones en la aplicación (in-app)."""

from __future__ import annotations

from datetime import datetime, timezone

from sirue.domain.entities.coincidencia import Coincidencia
from sirue.domain.entities.reporte_objeto import ReporteObjeto
from sirue.domain.entities.usuario import Usuario
from sirue.domain.ports.notificacion_service import NotificacionService


class InAppNotificationService(NotificacionService):
    """Servicio de notificaciones en memoria para el MVP.

    Almacena notificaciones en una lista en memoria en lugar de
    enviar correos electrónicos u otros canales externos.
    """

    def __init__(self) -> None:
        """Inicializa el servicio con una lista vacía de notificaciones."""
        self._notificaciones: list[dict] = []

    def notificar_coincidencia(
        self,
        usuario: Usuario,
        coincidencia: Coincidencia,
        reporte_propio: ReporteObjeto,
        reporte_match: ReporteObjeto,
    ) -> None:
        """Crea una notificación in-app sobre una coincidencia detectada.

        Args:
            usuario: Usuario destinatario de la notificación.
            coincidencia: Coincidencia detectada entre reportes.
            reporte_propio: Reporte del usuario notificado.
            reporte_match: Reporte que coincide con el del usuario.
        """
        mensaje = (
            f"Se encontró una posible coincidencia para tu reporte "
            f'"{reporte_propio.titulo}". '
            f'El objeto "{reporte_match.titulo}" tiene una puntuación '
            f"de coincidencia del {coincidencia.puntuacion:.0%}."
        )

        notificacion: dict = {
            "usuario_id": usuario.id,
            "mensaje": mensaje,
            "coincidencia_id": coincidencia.id,
            "fecha": datetime.now(timezone.utc).isoformat(),
            "leido": False,
        }
        self._notificaciones.append(notificacion)

    def obtener_notificaciones(self, usuario_id: str) -> list[dict]:
        """Obtiene todas las notificaciones de un usuario.

        Args:
            usuario_id: Identificador del usuario.

        Returns:
            Lista de notificaciones del usuario.
        """
        return [
            n for n in self._notificaciones if n["usuario_id"] == usuario_id
        ]

    def marcar_leida(self, notificacion_index: int) -> None:
        """Marca una notificación como leída por su índice.

        Args:
            notificacion_index: Índice de la notificación en la lista.
        """
        if 0 <= notificacion_index < len(self._notificaciones):
            self._notificaciones[notificacion_index]["leido"] = True

    def contar_no_leidas(self, usuario_id: str) -> int:
        """Cuenta las notificaciones no leídas de un usuario.

        Args:
            usuario_id: Identificador del usuario.

        Returns:
            Número de notificaciones sin leer.
        """
        return sum(
            1
            for n in self._notificaciones
            if n["usuario_id"] == usuario_id and not n["leido"]
        )
