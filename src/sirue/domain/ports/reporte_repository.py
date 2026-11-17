"""Puerto (interfaz) del repositorio de reportes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)


class ReporteRepository(ABC):
    """Interfaz abstracta para la persistencia de reportes de objetos.

    Define las operaciones que cualquier implementación de
    repositorio de reportes debe soportar.
    """

    @abstractmethod
    def guardar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        """Persiste un reporte de objeto."""
        ...

    @abstractmethod
    def obtener_por_id(self, id: str) -> Optional[ReporteObjeto]:
        """Obtiene un reporte por su ID."""
        ...

    @abstractmethod
    def listar_todos(self) -> list[ReporteObjeto]:
        """Lista todos los reportes registrados sin filtro."""
        ...

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str) -> list[ReporteObjeto]:
        """Lista todos los reportes de un usuario."""
        ...

    @abstractmethod
    def listar_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        """Lista todos los reportes de un tipo específico."""
        ...

    @abstractmethod
    def listar_activos(self) -> list[ReporteObjeto]:
        """Lista todos los reportes activos."""
        ...

    @abstractmethod
    def listar_activos_por_tipo(self, tipo: TipoReporte) -> list[ReporteObjeto]:
        """Lista todos los reportes activos de un tipo específico."""
        ...

    @abstractmethod
    def listar_por_estado(self, estado: EstadoReporte) -> list[ReporteObjeto]:
        """Lista todos los reportes que tengan un estado específico."""
        ...

    @abstractmethod
    def actualizar(self, reporte: ReporteObjeto) -> ReporteObjeto:
        """Actualiza un reporte existente."""
        ...
