"""Pruebas unitarias para MotorCoincidencias en la capa de aplicación."""

from datetime import datetime, timedelta, timezone
import unittest
import uuid

from sirue.application.services.motor_coincidencias import MotorCoincidencias
from sirue.domain.entities.reporte_objeto import ReporteObjeto, TipoReporte
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus


class TestMotorCoincidencias(unittest.TestCase):
    """Pruebas sobre el motor heurístico de afinidad y coincidencias."""

    def setUp(self) -> None:
        self.motor = MotorCoincidencias()
        self.ahora = datetime.now(timezone.utc) - timedelta(hours=2)

    def _crear_reporte(
        self,
        tipo: TipoReporte,
        titulo: str,
        descripcion: str,
        categoria: CategoriaObjeto,
        ref: str,
        fecha: datetime,
    ) -> ReporteObjeto:
        return ReporteObjeto(
            id=str(uuid.uuid4()),
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            ubicacion=UbicacionCampus(referencia_interna=ref),
            fecha_hora_incidente=FechaHoraIncidente(fecha),
            usuario_id=str(uuid.uuid4()),
        )

    def test_ponderaciones_suman_uno(self) -> None:
        total_pesos = (
            self.motor.PESO_CATEGORIA
            + self.motor.PESO_PALABRAS
            + self.motor.PESO_DISTANCIA
            + self.motor.PESO_TIEMPO
        )
        self.assertAlmostEqual(total_pesos, 1.0, places=4)

    def test_puntuacion_perfecta_reportes_identicos_en_todo(self) -> None:
        # Misma ubicación (< 100m / misma referencia), mismo momento (< 1h), misma categoría, mismas palabras
        rep_perdido = self._crear_reporte(
            tipo=TipoReporte.PERDIDO,
            titulo="Mochila Totto roja",
            descripcion="Mochila Totto roja con parches",
            categoria=CategoriaObjeto.MOCHILA,
            ref="Aula A-203",
            fecha=self.ahora,
        )
        rep_encontrado = self._crear_reporte(
            tipo=TipoReporte.ENCONTRADO,
            titulo="Mochila Totto roja",
            descripcion="Mochila Totto roja con parches",
            categoria=CategoriaObjeto.MOCHILA,
            ref="Aula A-203",
            fecha=self.ahora,
        )
        score, detalles = self.motor.calcular_puntuacion(rep_perdido, rep_encontrado)

        self.assertEqual(detalles["categoria"], 1.0)
        self.assertEqual(detalles["palabras_clave"], 1.0)
        self.assertEqual(detalles["distancia"], 1.0)
        self.assertEqual(detalles["tiempo"], 1.0)
        self.assertAlmostEqual(score, 1.0, places=4)

    def test_puntuacion_cero_todo_discrepante(self) -> None:
        # Categorías distintas, sin palabras en común, referencias sin palabras compartidas, > 24 horas
        rep_perdido = self._crear_reporte(
            tipo=TipoReporte.PERDIDO,
            titulo="Laptop Dell Inspiron",
            descripcion="Portátil negro de ingeniería",
            categoria=CategoriaObjeto.LAPTOP,
            ref="Laboratorio Alfa",
            fecha=self.ahora - timedelta(hours=48),
        )
        rep_encontrado = self._crear_reporte(
            tipo=TipoReporte.ENCONTRADO,
            titulo="Bufanda verde lana",
            descripcion="Prenda de vestir de invierno",
            categoria=CategoriaObjeto.ROPA,
            ref="Gimnasio Techado",
            fecha=self.ahora,
        )
        score, detalles = self.motor.calcular_puntuacion(rep_perdido, rep_encontrado)

        self.assertEqual(detalles["categoria"], 0.0)
        self.assertEqual(detalles["distancia"], 0.0)
        self.assertEqual(detalles["tiempo"], 0.0)
        self.assertEqual(score, 0.0)

    def test_categoria_comodin_otro_otorga_puntaje_parcial(self) -> None:
        rep_perdido = self._crear_reporte(
            tipo=TipoReporte.PERDIDO,
            titulo="Objeto no identificado",
            descripcion="Elemento olvidado en la cafetería",
            categoria=CategoriaObjeto.OTRO,
            ref="Cafetería",
            fecha=self.ahora,
        )
        rep_encontrado = self._crear_reporte(
            tipo=TipoReporte.ENCONTRADO,
            titulo="Mochila azul",
            descripcion="Mochila encontrada cerca a mesas",
            categoria=CategoriaObjeto.MOCHILA,
            ref="Cafetería",
            fecha=self.ahora,
        )
        _, detalles = self.motor.calcular_puntuacion(rep_perdido, rep_encontrado)
        self.assertEqual(detalles["categoria"], 0.3)

    def test_buscar_coincidencias_filtra_por_umbral_y_ordena(self) -> None:
        rep_perdido = self._crear_reporte(
            tipo=TipoReporte.PERDIDO,
            titulo="Mochila negra Totto",
            descripcion="Mochila negra con tiras rojas",
            categoria=CategoriaObjeto.MOCHILA,
            ref="Aula A-203",
            fecha=self.ahora,
        )
        # Candidato 1: Muy parecido (misma ubicación, misma categoría)
        cand1 = self._crear_reporte(
            tipo=TipoReporte.ENCONTRADO,
            titulo="Mochila negra",
            descripcion="Mochila negra encontrada en aula",
            categoria=CategoriaObjeto.MOCHILA,
            ref="Aula A-203",
            fecha=self.ahora,
        )
        # Candidato 2: Diferente (otra categoría, otra ubicación)
        cand2 = self._crear_reporte(
            tipo=TipoReporte.ENCONTRADO,
            titulo="Celular Samsung",
            descripcion="Teléfono inteligente con pantalla rota",
            categoria=CategoriaObjeto.CELULAR,
            ref="Gimnasio",
            fecha=self.ahora - timedelta(hours=30),
        )

        matches = self.motor.buscar_coincidencias(
            rep_perdido, [cand1, cand2], umbral=0.4
        )

        # Debe incluir cand1 y descartar cand2 por debajo del umbral
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0].id, cand1.id)
        self.assertTrue(matches[0][1] >= 0.4)

    def test_similitud_difusa_tolera_errores_tipograficos_y_prefijos(self) -> None:
        """Verifica que errores tipográficos como 'lapto' vs 'laptop' o 'bloue b' vs 'bloque b' coincidan."""
        rep_p = self._crear_reporte(
            tipo=TipoReporte.PERDIDO,
            titulo="Mi lapto Lenovo",
            descripcion="Lapto negra olvidada",
            categoria=CategoriaObjeto.LAPTOP,
            ref="Bloue B - B003",
            fecha=self.ahora,
        )
        rep_e = self._crear_reporte(
            tipo=TipoReporte.ENCONTRADO,
            titulo="Laptop Lenovo negra",
            descripcion="Laptop encontrada en aula",
            categoria=CategoriaObjeto.LAPTOP,
            ref="Bloque B - B003",
            fecha=self.ahora,
        )
        score, detalles = self.motor.calcular_puntuacion(rep_p, rep_e)
        self.assertGreaterEqual(score, 0.75)
        self.assertIn("Texto similar", detalles["etiquetas"])
        self.assertIn("Misma zona del campus", detalles["etiquetas"])


if __name__ == "__main__":
    unittest.main()
