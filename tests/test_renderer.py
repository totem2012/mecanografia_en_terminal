"""Tests del ajuste de líneas y la clasificación de caracteres del renderer."""

import unittest

from typing_trainer import renderer


class TestAjustarLineas(unittest.TestCase):
    def setUp(self):
        # El ajuste se cachea por (texto, ancho); limpiamos entre tests.
        renderer._cache_ajuste = {"clave": None, "lineas": None}

    def _reconstruir(self, texto, ancho):
        rangos = renderer._ajustar_lineas(texto, ancho)
        return [texto[a:b] for (a, b) in rangos]

    def test_texto_que_cabe_en_una_linea(self):
        self.assertEqual(renderer._ajustar_lineas("hola", 20), [(0, 4)])

    def test_cobertura_completa_sin_solapamiento(self):
        texto = "uno dos tres cuatro cinco seis siete ocho"
        rangos = renderer._ajustar_lineas(texto, 12)
        # Los rangos deben cubrir el texto entero, contiguos y en orden.
        self.assertEqual(rangos[0][0], 0)
        self.assertEqual(rangos[-1][1], len(texto))
        for (a, b), (c, _) in zip(rangos, rangos[1:]):
            self.assertEqual(b, c)

    def test_corta_en_espacios_cuando_es_posible(self):
        lineas = self._reconstruir("hola mundo feliz", 11)
        # No debe partir "mundo" por la mitad.
        self.assertTrue(all(" " in l or len(l) <= 11 for l in lineas))
        self.assertEqual("".join(lineas), "hola mundo feliz")

    def test_texto_vacio(self):
        self.assertEqual(renderer._ajustar_lineas("", 20), [(0, 0)])

    def test_resultado_se_cachea(self):
        r1 = renderer._ajustar_lineas("texto de prueba", 10)
        r2 = renderer._ajustar_lineas("texto de prueba", 10)
        self.assertIs(r1, r2)


class TestEstiloDe(unittest.TestCase):
    def test_caracter_correcto(self):
        objetivo = list("casa")
        escrito = list("ca")
        # posición 0 ya escrita y correcta
        self.assertEqual(renderer._estilo_de(0, 2, objetivo, escrito), ("correcto", "c"))

    def test_caracter_erroneo(self):
        objetivo = list("casa")
        escrito = list("ko")
        estilo, _ = renderer._estilo_de(0, 2, objetivo, escrito)
        self.assertEqual(estilo, "error")

    def test_espacio_erroneo_se_muestra_como_guion(self):
        objetivo = list("a a")
        escrito = list("ax")  # se escribió 'x' donde iba ' '
        estilo, visible = renderer._estilo_de(1, 2, objetivo, escrito)
        self.assertEqual(estilo, "error")
        self.assertEqual(visible, "_")

    def test_caracter_actual(self):
        objetivo = list("casa")
        self.assertEqual(renderer._estilo_de(2, 2, objetivo, list("ca")), ("actual", "s"))

    def test_caracter_pendiente(self):
        objetivo = list("casa")
        self.assertEqual(renderer._estilo_de(3, 2, objetivo, list("ca")), ("pendiente", "a"))


class TestBarra(unittest.TestCase):
    def test_vacia(self):
        self.assertIn("0%", renderer._barra(0, ancho=10))

    def test_llena(self):
        barra = renderer._barra(100, ancho=10)
        self.assertIn("100%", barra)
        self.assertEqual(barra.count("█"), 10)

    def test_intermedia(self):
        barra = renderer._barra(50, ancho=10)
        self.assertEqual(barra.count("█"), 5)


if __name__ == "__main__":
    unittest.main()
