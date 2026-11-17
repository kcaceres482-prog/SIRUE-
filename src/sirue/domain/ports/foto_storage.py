"""Puerto (interfaz) del servicio de almacenamiento de fotos."""

from __future__ import annotations

from abc import ABC, abstractmethod


class FotoStorage(ABC):
    """Interfaz abstracta para el almacenamiento de fotos de objetos.

    Define las operaciones de almacenamiento de archivos de imagen
    asociados a los reportes de objetos encontrados.
    """

    @abstractmethod
    def guardar_foto(self, archivo_bytes: bytes, nombre_archivo: str) -> str:
        """Guarda una foto y retorna su ruta.

        Args:
            archivo_bytes: Contenido binario del archivo de imagen.
            nombre_archivo: Nombre original del archivo.

        Returns:
            Ruta donde se almacenó la foto.
        """
        ...

    @abstractmethod
    def obtener_ruta(self, nombre_archivo: str) -> str:
        """Obtiene la ruta completa de una foto almacenada.

        Args:
            nombre_archivo: Nombre del archivo de foto.

        Returns:
            Ruta completa al archivo.
        """
        ...

    @abstractmethod
    def eliminar_foto(self, nombre_archivo: str) -> None:
        """Elimina una foto almacenada.

        Args:
            nombre_archivo: Nombre del archivo de foto a eliminar.
        """
        ...
