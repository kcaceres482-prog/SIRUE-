"""Pruebas unitarias para las Entidades del dominio SIRUE."""

from datetime import datetime, timedelta, timezone
import unittest
import uuid

from sirue.domain.entities.coincidencia import Coincidencia, EstadoCoincidencia
from sirue.domain.entities.reporte_objeto import (
    EstadoReporte,
    ReporteObjeto,
    TipoReporte,
)
from sirue.domain.entities.usuario import Usuario
from sirue.domain.exceptions.domain_exceptions import ValidacionError
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus


class TestUsuario(unittest.TestCase):
    """Pruebas sobre la Entidad Usuario."""

    def test_creacion_usuario_valido(self) -> None:
        user_id = str(uuid.uuid4())
        usuario = Usuario(
            id=user_id,
            nombre="Carlos Gómez",
            email="carlos.gomez@uab.edu.bo",
            telefono="+573001234567",
        )
        self.assertEqual(usuario.id, user_id)
        self.assertEqual(usuario.nombre, "Carlos Gómez")
        self.assertEqual(usuario.email, "carlos.gomez@uab.edu.bo")
        self.assertEqual(usuario.telefono, "+573001234567")
        self.assertIsInstance(usuario.fecha_registro, datetime)

    def test_nombre_vacio_falla(self) -> None:
        with self.assertRaises(ValidacionError):
            Usuario(id=str(uuid.uuid4()), nombre="", email="test@uab.edu.bo")

        with self.assertRaises(ValidacionError):
            Usuario(id=str(uuid.uuid4()), nombre="   ", email="test@uab.edu.bo")

    def test_email_invalido_falla(self) -> None:
        with self.assertRaises(ValidacionError):
            Usuario(id=str(uuid.uuid4()), nombre="Ana", email="correo_sin_arroba")

        with self.assertRaises(ValidacionError):
            Usuario(id=str(uuid.uuid4()), nombre="Ana", email="@sinusuario.com")

        with self.assertRaises(ValidacionError):
            Usuario(id=str(uuid.uuid4()), nombre="Ana", email="ana@gmail.com")

    def test_igualdad_por_identidad(self) -> None:
        uid = str(uuid.uuid4())
        u1 = Usuario(id=uid, nombre="A", email="a@uab.edu.bo")
        u2 = Usuario(id=uid, nombre="B", email="b@uab.edu.bo")
        self.assertEqual(u1, u2)
        self.assertEqual(hash(u1), hash(u2))


class TestReporteObjeto(unittest.TestCase):
    """Pruebas sobre la Entidad ReporteObjeto."""

    def setUp(self) -> None:
        self.ubicacion = UbicacionCampus(referencia_interna="Aula A-203")
        self.fecha_incidente = FechaHoraIncidente(
            datetime.now(timezone.utc) - timedelta(hours=2)
        )

    def test_creacion_reporte_perdido(self) -> None:
        rep_id = str(uuid.uuid4())
        usuario_id = str(uuid.uuid4())
        reporte = ReporteObjeto(
            id=rep_id,
            tipo=TipoReporte.PERDIDO,
            titulo="Mochila azul marca Jansport",
            descripcion="Olvidada en el pupitre del fondo con una libreta y cartuchera",
            categoria=CategoriaObjeto.MOCHILA,
            ubicacion=self.ubicacion,
            fecha_hora_incidente=self.fecha_incidente,
            usuario_id=usuario_id,
        )
        self.assertEqual(reporte.id, rep_id)
        self.assertEqual(reporte.tipo, TipoReporte.PERDIDO)
        self.assertTrue(reporte.esta_activo())
        self.assertEqual(reporte.estado, EstadoReporte.ACTIVO)
        self.assertIsNone(reporte.foto_ruta)

    def test_extraccion_automatica_palabras_clave(self) -> None:
        reporte = ReporteObjeto(
            id=str(uuid.uuid4()),
            tipo=TipoReporte.PERDIDO,
            titulo="Laptop Lenovo ThinkPad negra",
            descripcion="Se quedó en la mesa central, tiene calcomanía de Python",
            categoria=CategoriaObjeto.LAPTOP,
            ubicacion=self.ubicacion,
            fecha_hora_incidente=self.fecha_incidente,
            usuario_id=str(uuid.uuid4()),
        )
        palabras = reporte.palabras_clave
        self.assertIn("laptop", palabras)
        self.assertIn("lenovo", palabras)
        self.assertIn("thinkpad", palabras)
        self.assertIn("negra", palabras)
        self.assertIn("python", palabras)
        # Stopwords no deben estar presentes
        self.assertNotIn("la", palabras)
        self.assertNotIn("en", palabras)
        self.assertNotIn("se", palabras)

    def test_marcar_como_resuelto(self) -> None:
        reporte = ReporteObjeto(
            id=str(uuid.uuid4()),
            tipo=TipoReporte.PERDIDO,
            titulo="Calculadora Casio",
            descripcion="Calculadora científica plateada fx-991LA",
            categoria=CategoriaObjeto.OTRO,
            ubicacion=self.ubicacion,
            fecha_hora_incidente=self.fecha_incidente,
            usuario_id=str(uuid.uuid4()),
        )
        self.assertTrue(reporte.esta_activo())
        reporte.marcar_resuelto()
        self.assertFalse(reporte.esta_activo())
        self.assertEqual(reporte.estado, EstadoReporte.RESUELTO)


class TestCoincidencia(unittest.TestCase):
    """Pruebas sobre la Entidad Coincidencia."""

    def test_creacion_valida(self) -> None:
        c_id = str(uuid.uuid4())
        p_id = str(uuid.uuid4())
        e_id = str(uuid.uuid4())
        coincidencia = Coincidencia(
            id=c_id,
            reporte_perdido_id=p_id,
            reporte_encontrado_id=e_id,
            puntuacion=0.85,
            detalles={"categoria": 1.0, "espacio": 0.9, "tiempo": 0.7},
        )
        self.assertEqual(coincidencia.id, c_id)
        self.assertEqual(coincidencia.puntuacion, 0.85)
        self.assertEqual(coincidencia.estado, EstadoCoincidencia.PENDIENTE)
        self.assertTrue(coincidencia.es_relevante(umbral=0.7))

    def test_puntuacion_invalida_lanza_error(self) -> None:
        with self.assertRaises(ValidacionError):
            Coincidencia(
                id=str(uuid.uuid4()),
                reporte_perdido_id=str(uuid.uuid4()),
                reporte_encontrado_id=str(uuid.uuid4()),
                puntuacion=1.5,
            )

        with self.assertRaises(ValidacionError):
            Coincidencia(
                id=str(uuid.uuid4()),
                reporte_perdido_id=str(uuid.uuid4()),
                reporte_encontrado_id=str(uuid.uuid4()),
                puntuacion=-0.1,
            )

    def test_confirmar_y_descartar(self) -> None:
        coin = Coincidencia(
            id=str(uuid.uuid4()),
            reporte_perdido_id=str(uuid.uuid4()),
            reporte_encontrado_id=str(uuid.uuid4()),
            puntuacion=0.92,
        )
        self.assertEqual(coin.estado, EstadoCoincidencia.PENDIENTE)

        coin.confirmar()
        self.assertEqual(coin.estado, EstadoCoincidencia.CONFIRMADA)

        coin.descartar()
        self.assertEqual(coin.estado, EstadoCoincidencia.DESCARTADA)

    def test_es_relevante_evalua_umbral(self) -> None:
        c_baja = Coincidencia(
            id=str(uuid.uuid4()),
            reporte_perdido_id=str(uuid.uuid4()),
            reporte_encontrado_id=str(uuid.uuid4()),
            puntuacion=0.35,
        )
        self.assertFalse(c_baja.es_relevante(umbral=0.5))
        self.assertTrue(c_baja.es_relevante(umbral=0.3))


if __name__ == "__main__":
    unittest.main()
