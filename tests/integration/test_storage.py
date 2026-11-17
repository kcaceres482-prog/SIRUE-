"""Pruebas de integración para el almacenamiento local de fotos."""

import os
from pathlib import Path
import shutil
import tempfile
import unittest

from sirue.infrastructure.storage.local_photo_storage import LocalPhotoStorage


class TestLocalPhotoStorage(unittest.TestCase):
    """Pruebas sobre el adaptador LocalPhotoStorage."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.storage = LocalPhotoStorage(base_path=self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_guardar_y_obtener_foto(self) -> None:
        contenido = b"\x89PNG\r\n\x1a\n...bytes_simulados_de_imagen"
        ruta_relativa = self.storage.guardar_foto(
            archivo_bytes=contenido,
            nombre_archivo="mochila_encontrada.png",
        )

        self.assertTrue(ruta_relativa.endswith(".png"))
        nombre_guardado = Path(ruta_relativa).name
        ruta_completa = self.storage.obtener_ruta(nombre_guardado)

        self.assertTrue(os.path.exists(ruta_completa))
        with open(ruta_completa, "rb") as f:
            self.assertEqual(f.read(), contenido)

    def test_eliminar_foto(self) -> None:
        contenido = b"foto_a_eliminar"
        ruta_relativa = self.storage.guardar_foto(contenido, "temp.jpg")
        nombre_guardado = Path(ruta_relativa).name
        ruta_completa = self.storage.obtener_ruta(nombre_guardado)

        self.assertTrue(os.path.exists(ruta_completa))
        self.storage.eliminar_foto(nombre_guardado)
        self.assertFalse(os.path.exists(ruta_completa))

    def test_eliminar_foto_inexistente_no_falla(self) -> None:
        # No debe lanzar excepción
        self.storage.eliminar_foto("archivo_inexistente.jpg")


if __name__ == "__main__":
    unittest.main()
