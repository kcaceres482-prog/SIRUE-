"""Implementación de almacenamiento local de fotos."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from sirue.domain.ports.foto_storage import FotoStorage


class LocalPhotoStorage(FotoStorage):
    """Almacenamiento de fotos en el sistema de archivos local."""

    def __init__(self, base_path: str = "uploads") -> None:
        """Inicializa el almacenamiento local de fotos.

        Crea el directorio base si no existe.

        Args:
            base_path: Ruta base donde se almacenarán las fotos.
        """
        self._base_path = Path(base_path)
        self._base_path.mkdir(parents=True, exist_ok=True)

    def guardar_foto(self, archivo_bytes: bytes, nombre_archivo: str) -> str:
        """Guarda una foto en el sistema de archivos local.

        Genera un nombre único usando UUID para evitar colisiones,
        conservando la extensión original del archivo.

        Args:
            archivo_bytes: Contenido binario de la foto.
            nombre_archivo: Nombre original del archivo (para extraer extensión).

        Returns:
            Ruta relativa al archivo guardado.
        """
        extension = Path(nombre_archivo).suffix
        nombre_unico = f"{uuid.uuid4().hex}{extension}"
        ruta_completa = self._base_path / nombre_unico

        with open(ruta_completa, "wb") as f:
            f.write(archivo_bytes)

        return str(Path(self._base_path.name) / nombre_unico)

    def obtener_ruta(self, nombre_archivo: str) -> str:
        """Obtiene la ruta completa de una foto almacenada.

        Args:
            nombre_archivo: Nombre del archivo almacenado.

        Returns:
            Ruta completa al archivo.
        """
        return str(self._base_path / nombre_archivo)

    def eliminar_foto(self, nombre_archivo: str) -> None:
        """Elimina una foto del sistema de archivos local.

        No lanza error si el archivo no existe.

        Args:
            nombre_archivo: Nombre del archivo a eliminar.
        """
        ruta = self._base_path / nombre_archivo
        if ruta.exists():
            os.remove(ruta)
