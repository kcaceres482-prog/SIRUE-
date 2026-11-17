"""Pruebas unitarias para ReporteFactory en la capa de aplicación."""

from datetime import datetime, timezone
import unittest
import uuid

from sirue.application.dtos.reporte_dto import ReporteInputDTO
from sirue.application.factories.reporte_factory import ReporteFactory
from sirue.domain.entities.reporte_objeto import EstadoReporte, TipoReporte
from sirue.domain.exceptions.domain_exceptions import (
    DescripcionInsuficienteError,
    FotoRequeridaError,
    ValidacionError,
)
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto


class TestReporteFactory(unittest.TestCase):
    """Pruebas unitarias sobre la fábrica de reportes."""

    def setUp(self) -> None:
        self.usuario_id = str(uuid.uuid4())
        self.ahora_iso = datetime.now(timezone.utc).isoformat()

    def test_crear_reporte_perdido_valido(self) -> None:
        dto = ReporteInputDTO(
            titulo="Mochila Totto negra",
            descripcion="Mochila con cremalleras rojas dejada en el aula de cálculo",
            categoria_str="MOCHILA",
            referencia="Aula A-203",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.usuario_id,
        )
        reporte = ReporteFactory.crear_reporte_perdido(dto)

        self.assertIsNotNone(reporte.id)
        self.assertEqual(reporte.tipo, TipoReporte.PERDIDO)
        self.assertEqual(reporte.titulo, "Mochila Totto negra")
        self.assertEqual(reporte.categoria, CategoriaObjeto.MOCHILA)
        self.assertEqual(reporte.ubicacion.referencia_interna, "Aula A-203")
        self.assertEqual(reporte.estado, EstadoReporte.ACTIVO)
        self.assertIsNone(reporte.foto_ruta)
        self.assertTrue(len(reporte.palabras_clave) > 0)

    def test_crear_reporte_perdido_descripcion_corta_permitida(self) -> None:
        dto = ReporteInputDTO(
            titulo="Mochila",
            descripcion="Mochila corta",  # Menos de 20 caracteres permitida
            categoria_str="MOCHILA",
            referencia="Aula A-203",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.usuario_id,
        )
        reporte = ReporteFactory.crear_reporte_perdido(dto)
        self.assertEqual(reporte.descripcion, "Mochila corta")
        self.assertEqual(reporte.titulo, "Mochila")

    def test_crear_reporte_perdido_titulo_vacio_falla(self) -> None:
        dto = ReporteInputDTO(
            titulo="   ",
            descripcion="Descripción suficientemente larga con más de veinte caracteres",
            categoria_str="MOCHILA",
            referencia="Aula A-203",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.usuario_id,
        )
        with self.assertRaises(ValidacionError):
            ReporteFactory.crear_reporte_perdido(dto)

    def test_crear_reporte_encontrado_valido(self) -> None:
        dto = ReporteInputDTO(
            titulo="Llaves con llavero de Superman",
            descripcion="Encontradas en el jardín central",
            categoria_str="LLAVES",
            referencia="Jardín Central",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.usuario_id,
            foto_bytes=b"\xFF\xD8\xFF\xE0...imagen_simulada",
            foto_nombre="llaves.jpg",
        )
        reporte = ReporteFactory.crear_reporte_encontrado(dto)

        self.assertIsNotNone(reporte.id)
        self.assertEqual(reporte.tipo, TipoReporte.ENCONTRADO)
        self.assertEqual(reporte.categoria, CategoriaObjeto.LLAVES)

    def test_crear_reporte_encontrado_sin_foto_falla(self) -> None:
        dto = ReporteInputDTO(
            titulo="Llaves",
            descripcion="Encontradas sin foto",
            categoria_str="LLAVES",
            referencia="Jardín Central",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.usuario_id,
            foto_bytes=None,  # Sin foto obligatoria
        )
        with self.assertRaises(FotoRequeridaError):
            ReporteFactory.crear_reporte_encontrado(dto)

    def test_categoria_invalida_falla(self) -> None:
        dto = ReporteInputDTO(
            titulo="Objeto X",
            descripcion="Descripción suficientemente larga para pruebas unitarias",
            categoria_str="CATEGORIA_INVENTADA",
            referencia="Patio",
            fecha_hora_str=self.ahora_iso,
            usuario_id=self.usuario_id,
        )
        with self.assertRaises(ValidacionError):
            ReporteFactory.crear_reporte_perdido(dto)


if __name__ == "__main__":
    unittest.main()
