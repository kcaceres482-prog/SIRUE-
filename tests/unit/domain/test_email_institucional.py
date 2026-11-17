"""Pruebas unitarias para la validación centralizada y Value Object EmailInstitucional."""

import unittest

from sirue.domain.exceptions.domain_exceptions import ValidacionError
from sirue.domain.value_objects.email_institucional import (
    DOMINIO_INSTITUCIONAL,
    EmailInstitucional,
    es_email_institucional_valido,
    normalizar_email,
    validar_formato_email_institucional,
)


class TestEmailInstitucional(unittest.TestCase):
    """Pruebas para validación y comportamiento del correo institucional UAB."""

    def test_correos_validos_permitidos(self) -> None:
        validos = [
            "estudiante@uab.edu.bo",
            "administrador@uab.edu.bo",
            "carlos.gomez@uab.edu.bo",
            "ana_laura-2026@uab.edu.bo",
            "docente+sirue@uab.edu.bo",
        ]
        for email in validos:
            res = validar_formato_email_institucional(email)
            self.assertEqual(res, email)
            self.assertTrue(es_email_institucional_valido(email))

    def test_normalizacion_espacios_y_mayusculas(self) -> None:
        entrada = "   Estudiante.Prueba@UAB.EDU.BO   "
        esperado = "estudiante.prueba@uab.edu.bo"
        self.assertEqual(normalizar_email(entrada), esperado)
        self.assertEqual(validar_formato_email_institucional(entrada), esperado)
        self.assertTrue(es_email_institucional_valido(entrada))

    def test_rechazo_correos_externos(self) -> None:
        externos = [
            "usuario@gmail.com",
            "usuario@hotmail.com",
            "usuario@outlook.com",
            "usuario@uab.com",
            "usuario@edu.bo",
            "usuario@campus.edu",
            "usuario@yahoo.es",
            "usuario@sub.uab.edu.bo",
        ]
        for email in externos:
            self.assertFalse(
                es_email_institucional_valido(email),
                f"El correo externo {email} no debería ser válido",
            )
            with self.assertRaises(ValidacionError) as ctx:
                validar_formato_email_institucional(email)
            self.assertIn("Solo se permiten correos institucionales con dominio @uab.edu.bo", str(ctx.exception))

    def test_rechazo_correos_malformados(self) -> None:
        malformados = [
            "correo_sin_arroba",
            "@uab.edu.bo",
            "usuario@@uab.edu.bo",
            "usuario@uab@edu.bo",
            "usuario con espacios@uab.edu.bo",
        ]
        for email in malformados:
            self.assertFalse(es_email_institucional_valido(email))
            with self.assertRaises(ValidacionError):
                validar_formato_email_institucional(email)

    def test_rechazo_correo_vacio_o_nulo(self) -> None:
        with self.assertRaises(ValidacionError):
            validar_formato_email_institucional("")
        with self.assertRaises(ValidacionError):
            validar_formato_email_institucional("   ")
        with self.assertRaises(ValidacionError):
            validar_formato_email_institucional(None)

        self.assertFalse(es_email_institucional_valido(""))
        self.assertFalse(es_email_institucional_valido(None))

    def test_value_object_inmutable(self) -> None:
        vo = EmailInstitucional("  Estudiante@UAB.EDU.BO  ")
        self.assertEqual(vo.valor, "estudiante@uab.edu.bo")
        self.assertEqual(str(vo), "estudiante@uab.edu.bo")
        self.assertEqual(repr(vo), "EmailInstitucional('estudiante@uab.edu.bo')")

        vo2 = EmailInstitucional("estudiante@uab.edu.bo")
        self.assertEqual(vo, vo2)
        self.assertEqual(hash(vo), hash(vo2))


if __name__ == "__main__":
    unittest.main()
