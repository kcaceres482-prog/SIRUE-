"""DTOs (Data Transfer Objects) para la capa de aplicación."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ReporteInputDTO:
    """DTO de entrada para la creación de un reporte.

    Contiene los datos necesarios proporcionados por la UI
    para crear un nuevo reporte de objeto perdido o encontrado.

    Attributes:
        titulo: Título descriptivo del reporte.
        descripcion: Descripción detallada del objeto.
        categoria_str: Nombre de la categoría como cadena (ej: 'MOCHILA').
        referencia: Referencia interna o lugar del campus (ej: 'Aula A-203', 'Cafetería').
        fecha_hora_str: Fecha y hora del incidente en formato ISO 8601.
        usuario_id: UUID del usuario que reporta.
        foto_bytes: Contenido binario de la foto (obligatorio para hallazgos).
        foto_nombre: Nombre del archivo de foto (opcional).
    """

    titulo: str
    descripcion: str
    categoria_str: str
    referencia: str
    fecha_hora_str: str
    usuario_id: str
    foto_bytes: Optional[bytes] = None
    foto_nombre: Optional[str] = None


@dataclass
class ReporteOutputDTO:
    """DTO de salida con los datos de un reporte para la UI.

    Attributes:
        id: UUID del reporte.
        tipo: Tipo de reporte ('PERDIDO' o 'ENCONTRADO').
        titulo: Título del reporte.
        descripcion: Descripción detallada.
        categoria: Nombre de la categoría.
        referencia: Referencia o lugar en el campus.
        fecha_hora_incidente: Fecha y hora del incidente (ISO 8601).
        usuario_id: UUID del usuario creador.
        nombre_usuario: Nombre del usuario creador.
        foto_ruta: Ruta a la foto (si existe).
        palabras_clave: Lista de palabras clave.
        estado: Estado del reporte.
        fecha_creacion: Fecha de creación del reporte (ISO 8601).
    """

    id: str
    tipo: str
    titulo: str
    descripcion: str
    categoria: str
    referencia: str
    fecha_hora_incidente: str
    usuario_id: str
    nombre_usuario: str
    foto_ruta: Optional[str] = None
    palabras_clave: list[str] = field(default_factory=list)
    estado: str = "ACTIVO"
    fecha_creacion: str = ""


@dataclass
class CoincidenciaOutputDTO:
    """DTO de salida con los datos de una coincidencia para la UI.

    Attributes:
        id: UUID de la coincidencia.
        reporte_perdido_id: UUID del reporte perdido.
        reporte_encontrado_id: UUID del reporte encontrado.
        puntuacion: Puntuación de coincidencia (0.0 a 1.0).
        estado: Estado de la coincidencia.
        fecha_deteccion: Fecha de detección (ISO 8601).
        detalles: Desglose de la puntuación por criterio.
        titulo_perdido: Título del reporte perdido.
        titulo_encontrado: Título del reporte encontrado.
    """

    id: str
    reporte_perdido_id: str
    reporte_encontrado_id: str
    puntuacion: float
    estado: str
    fecha_deteccion: str
    detalles: dict = field(default_factory=dict)
    titulo_perdido: str = ""
    titulo_encontrado: str = ""
