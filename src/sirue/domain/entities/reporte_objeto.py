"""Entidad que representa un reporte de objeto perdido o encontrado con ciclo de vida extendido."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus


class TipoReporte(Enum):
    """Tipo de reporte: objeto perdido o encontrado."""
    PERDIDO = "PERDIDO"
    ENCONTRADO = "ENCONTRADO"


class EstadoReporte(Enum):
    """Estado actual del reporte en su ciclo de vida."""
    ACTIVO = "ACTIVO"
    EN_PROCESO = "EN_PROCESO"
    RECUPERADO = "RECUPERADO"
    CERRADO = "CERRADO"
    RESUELTO = "RESUELTO"  # Mantenido para retrocompatibilidad


# Stopwords básicas del español para extracción de palabras clave
_STOPWORDS_ES: set[str] = {
    "a", "al", "algo", "con", "como", "cual", "de", "del", "el", "ella",
    "en", "era", "es", "esa", "ese", "eso", "esta", "este", "esto",
    "fue", "ha", "hay", "la", "las", "le", "les", "lo", "los", "mas",
    "me", "mi", "muy", "no", "nos", "otra", "otro", "para",
    "pero", "por", "que", "se", "ser", "si", "sin", "sobre", "son",
    "su", "sus", "te", "tu", "tus", "un", "una", "uno", "unas", "unos",
    "ya", "yo", "y", "o", "ni",
}


class ReporteObjeto:
    """Reporte de un objeto perdido o encontrado en el campus.

    Attributes:
        id: Identificador único (UUID).
        tipo: Tipo de reporte (PERDIDO o ENCONTRADO).
        titulo: Título descriptivo del reporte.
        descripcion: Descripción detallada del objeto y las circunstancias.
        categoria: Categoría del objeto.
        ubicacion: Ubicación del campus donde se perdió/encontró.
        fecha_hora_incidente: Fecha y hora del incidente.
        usuario_id: ID del usuario que creó el reporte.
        foto_ruta: Ruta a la foto del objeto (opcional).
        palabras_clave: Lista de palabras clave extraídas del reporte.
        estado: Estado actual del reporte.
        fecha_creacion: Fecha y hora de creación del reporte.
    """

    def __init__(
        self,
        id: str,
        tipo: TipoReporte,
        titulo: str,
        descripcion: str,
        categoria: CategoriaObjeto,
        ubicacion: UbicacionCampus,
        fecha_hora_incidente: FechaHoraIncidente,
        usuario_id: str,
        foto_ruta: Optional[str] = None,
        palabras_clave: Optional[list[str]] = None,
        estado: EstadoReporte = EstadoReporte.ACTIVO,
        fecha_creacion: Optional[datetime] = None,
    ) -> None:
        """Inicializa un reporte de objeto."""
        self.id = id
        self.tipo = tipo if isinstance(tipo, TipoReporte) else TipoReporte(tipo)
        self.titulo = titulo
        self.descripcion = descripcion
        self.categoria = (
            categoria
            if isinstance(categoria, CategoriaObjeto)
            else CategoriaObjeto(categoria)
        )
        self.ubicacion = ubicacion
        self.fecha_hora_incidente = fecha_hora_incidente
        self.usuario_id = usuario_id
        self.foto_ruta = foto_ruta
        self.estado = estado if isinstance(estado, EstadoReporte) else EstadoReporte(estado)
        self.fecha_creacion = fecha_creacion or datetime.now(timezone.utc)

        if palabras_clave is not None:
            self.palabras_clave = palabras_clave
        else:
            self.palabras_clave = self.extraer_palabras_clave()

    def extraer_palabras_clave(self) -> list[str]:
        """Extrae palabras clave del título y la descripción."""
        texto = f"{self.titulo} {self.descripcion}".lower()
        limpio: list[str] = []
        for char in texto:
            if char.isalnum() or char in "áéíóúñü":
                limpio.append(char)
            else:
                limpio.append(" ")
        palabras = "".join(limpio).split()

        resultado: list[str] = []
        vistas: set[str] = set()
        for p in palabras:
            if len(p) > 2 and p not in _STOPWORDS_ES and p not in vistas:
                resultado.append(p)
                vistas.add(p)

        return sorted(resultado)

    def cambiar_estado(self, nuevo_estado: EstadoReporte) -> None:
        """Actualiza el estado administrativo del reporte."""
        self.estado = nuevo_estado if isinstance(nuevo_estado, EstadoReporte) else EstadoReporte(nuevo_estado)

    def marcar_resuelto(self) -> None:
        """Marca el reporte como resuelto/recuperado."""
        self.estado = EstadoReporte.RESUELTO

    def esta_activo(self) -> bool:
        """Indica si el reporte está activo para cruces y visualización."""
        return self.estado == EstadoReporte.ACTIVO

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReporteObjeto):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return (
            f"ReporteObjeto(id={self.id!r}, tipo={self.tipo.value}, "
            f"titulo={self.titulo!r}, estado={self.estado.value})"
        )
