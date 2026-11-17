"""Puerto (interfaz) del servicio de notificaciones."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sirue.domain.entities.coincidencia import Coincidencia
from sirue.domain.entities.reporte_objeto import ReporteObjeto
from sirue.domain.entities.usuario import Usuario


class NotificacionService(ABC):
    """Interfaz abstracta para el servicio de notificaciones.

    Define cómo se notifica a los usuarios sobre coincidencias
    detectadas entre reportes.
    """

    @abstractmethod
    def notificar_coincidencia(
        self,
        usuario: Usuario,
        coincidencia: Coincidencia,
        reporte_propio: ReporteObjeto,
        reporte_match: ReporteObjeto,
    ) -> None:
        """Notifica a un usuario sobre una coincidencia detectada.

        Args:
            usuario: Usuario a notificar.
            coincidencia: La coincidencia detectada.
            reporte_propio: Reporte del usuario notificado.
            reporte_match: Reporte que coincide con el del usuario.
        """
        ...
