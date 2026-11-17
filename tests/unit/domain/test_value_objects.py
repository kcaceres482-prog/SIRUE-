"""Pruebas unitarias para los Value Objects del dominio SIRUE."""

from datetime import datetime, timedelta, timezone
import unittest

from sirue.domain.exceptions.domain_exceptions import ValidacionError
from sirue.domain.value_objects.categoria_objeto import CategoriaObjeto
from sirue.domain.value_objects.fecha_hora_incidente import FechaHoraIncidente
from sirue.domain.value_objects.ubicacion_campus import UbicacionCampus


class TestUbicacionCampus(unittest.TestCase):
    """Pruebas sobre el Value Object UbicacionCampus."""

    def test_creacion_valida(self) -> None:
        ubicacion = UbicacionCampus(referencia_interna="Aula A-203")
        self.assertEqual(ubicacion.referencia_interna, "Aula A-203")

    def test_referencia_interna_vacia(self) -> None:
        with self.assertRaises(ValidacionError):
            UbicacionCampus(referencia_interna="")

        with self.assertRaises(ValidacionError):
            UbicacionCampus(referencia_interna="   ")

    def test_inmutabilidad(self) -> None:
        u1 = UbicacionCampus(referencia_interna="Aula A-203")
        with self.assertRaises(Exception):  # FrozenInstanceError
            setattr(u1, "referencia_interna", "Otro lugar")

    def test_coincide_con_misma_referencia(self) -> None:
        u1 = UbicacionCampus(referencia_interna="Aula A-203")
        u2 = UbicacionCampus(referencia_interna="Aula A-203")
        self.assertEqual(u1.coincide_con(u2), 1.0)

    def test_coincide_con_referencia_diferente(self) -> None:
        u1 = UbicacionCampus(referencia_interna="Aula A-203")
        u2 = UbicacionCampus(referencia_interna="Biblioteca Central")
        self.assertEqual(u1.coincide_con(u2), 0.0)

    def test_coincide_con_palabras_parciales(self) -> None:
        u1 = UbicacionCampus(referencia_interna="Aula A-203")
        u2 = UbicacionCampus(referencia_interna="Pasillo Aula B")
        # Comparten "Aula" → Jaccard > 0
        self.assertGreater(u1.coincide_con(u2), 0.0)
        self.assertLess(u1.coincide_con(u2), 1.0)


class TestFechaHoraIncidente(unittest.TestCase):
    """Pruebas sobre el Value Object FechaHoraIncidente."""

    def test_creacion_valida(self) -> None:
        hace_una_hora = datetime.now(timezone.utc) - timedelta(hours=1)
        fecha = FechaHoraIncidente(hace_una_hora)
        self.assertEqual(fecha.valor, hace_una_hora)

    def test_requiere_timezone_aware(self) -> None:
        naive_dt = datetime.now()  # sin tzinfo
        with self.assertRaises(ValidacionError):
            FechaHoraIncidente(naive_dt)

    def test_fecha_en_el_futuro_invalida(self) -> None:
        en_el_futuro = datetime.now(timezone.utc) + timedelta(hours=2)
        with self.assertRaises(ValidacionError):
            FechaHoraIncidente(en_el_futuro)

    def test_margen_de_cinco_minutos_tolerado(self) -> None:
        desviacion_leve = datetime.now(timezone.utc) + timedelta(minutes=2)
        fecha = FechaHoraIncidente(desviacion_leve)
        self.assertEqual(fecha.valor, desviacion_leve)

    def test_calculo_diferencia_horas(self) -> None:
        base = datetime.now(timezone.utc) - timedelta(hours=5)
        f1 = FechaHoraIncidente(base)
        f2 = FechaHoraIncidente(base + timedelta(hours=3, minutes=30))
        self.assertAlmostEqual(f1.diferencia_horas(f2), 3.5, places=2)


class TestCategoriaObjeto(unittest.TestCase):
    """Pruebas sobre el Value Object CategoriaObjeto."""

    def test_categorias_definidas(self) -> None:
        self.assertEqual(CategoriaObjeto.MOCHILA.value, "MOCHILA")
        self.assertEqual(CategoriaObjeto.LAPTOP.value, "LAPTOP")
        self.assertEqual(CategoriaObjeto.CELULAR.value, "CELULAR")

    def test_compatibilidad_misma_categoria(self) -> None:
        self.assertTrue(CategoriaObjeto.MOCHILA.es_compatible(CategoriaObjeto.MOCHILA))
        self.assertTrue(CategoriaObjeto.CELULAR.es_compatible(CategoriaObjeto.CELULAR))

    def test_compatibilidad_con_comodin_otro(self) -> None:
        self.assertTrue(CategoriaObjeto.MOCHILA.es_compatible(CategoriaObjeto.OTRO))
        self.assertTrue(CategoriaObjeto.OTRO.es_compatible(CategoriaObjeto.LAPTOP))

    def test_incompatibilidad_categorias_distintas(self) -> None:
        self.assertFalse(CategoriaObjeto.MOCHILA.es_compatible(CategoriaObjeto.CELULAR))
        self.assertFalse(CategoriaObjeto.LIBRO.es_compatible(CategoriaObjeto.LLAVES))


if __name__ == "__main__":
    unittest.main()
