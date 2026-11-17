"""Pruebas unitarias para generación de enlaces de contacto y modal de detalles."""

import unittest

from sirue.presentation.components.modal_detalle_reporte import (
    generar_enlace_whatsapp,
    normalizar_telefono_whatsapp,
)


class TestContactoYWhatsApp(unittest.TestCase):
    """Pruebas sobre la normalización de números telefónicos y enlaces de WhatsApp."""

    def test_normalizar_telefono_8_digitos_agrega_codigo_591(self) -> None:
        self.assertEqual(normalizar_telefono_whatsapp("71234567"), "59171234567")
        self.assertEqual(normalizar_telefono_whatsapp("69876543"), "59169876543")

    def test_normalizar_telefono_con_espacios_y_simbolos(self) -> None:
        self.assertEqual(normalizar_telefono_whatsapp("+591 712-34567"), "59171234567")
        self.assertEqual(normalizar_telefono_whatsapp("591 71234567"), "59171234567")

    def test_normalizar_telefono_vacio_retorna_vacio(self) -> None:
        self.assertEqual(normalizar_telefono_whatsapp(""), "")
        self.assertEqual(normalizar_telefono_whatsapp("   "), "")

    def test_generar_enlace_whatsapp_incluye_titulo_y_numero(self) -> None:
        url = generar_enlace_whatsapp("71234567", "Calculadora Casio", "ENCONTRADO")
        self.assertTrue(url.startswith("https://wa.me/59171234567?text="))
        self.assertIn("Calculadora%20Casio", url)
        self.assertIn("SIRUE%20UAB", url)

    def test_generar_enlace_whatsapp_sin_telefono_retorna_vacio(self) -> None:
        url = generar_enlace_whatsapp("", "Objeto")
        self.assertEqual(url, "")


if __name__ == "__main__":
    unittest.main()
