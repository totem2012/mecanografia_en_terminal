"""Tests del teclado en pantalla (mapeo de teclas y resaltado)."""

import unittest

from typing_trainer import teclado


class TestTeclaFisica(unittest.TestCase):
    def test_letra_simple(self):
        self.assertEqual(teclado.tecla_fisica("a"), "A")

    def test_mayuscula(self):
        self.assertEqual(teclado.tecla_fisica("A"), "A")

    def test_vocal_acentuada_mapea_a_su_base(self):
        self.assertEqual(teclado.tecla_fisica("á"), "A")
        self.assertEqual(teclado.tecla_fisica("ó"), "O")
        self.assertEqual(teclado.tecla_fisica("ü"), "U")

    def test_enie_se_conserva(self):
        self.assertEqual(teclado.tecla_fisica("ñ"), "Ñ")
        self.assertEqual(teclado.tecla_fisica("Ñ"), "Ñ")

    def test_espacio(self):
        self.assertEqual(teclado.tecla_fisica(" "), " ")

    def test_caracter_fuera_del_teclado(self):
        # Signos y números no están en el teclado de solo letras.
        self.assertIsNone(teclado.tecla_fisica(","))
        self.assertIsNone(teclado.tecla_fisica("5"))
        self.assertIsNone(teclado.tecla_fisica(None))
        self.assertIsNone(teclado.tecla_fisica(""))


class TestLineas(unittest.TestCase):
    def test_devuelve_cuatro_filas(self):
        # Tres filas de letras + barra espaciadora.
        self.assertEqual(len(teclado.lineas()), 4)

    def test_resalta_acierto_en_verde(self):
        salida = "".join(teclado.lineas("a", True))
        self.assertIn(teclado._VERDE, salida)
        self.assertNotIn(teclado._ROJO, salida)

    def test_resalta_fallo_en_rojo(self):
        salida = "".join(teclado.lineas("a", False))
        self.assertIn(teclado._ROJO, salida)
        self.assertNotIn(teclado._VERDE, salida)

    def test_sin_tecla_no_resalta(self):
        salida = "".join(teclado.lineas(None, True))
        self.assertNotIn(teclado._VERDE, salida)
        self.assertNotIn(teclado._ROJO, salida)


if __name__ == "__main__":
    unittest.main()
