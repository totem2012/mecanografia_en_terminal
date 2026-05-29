"""Tests de las funciones puras de carga y troceado de textos."""

import unittest

from typing_trainer import textos


class TestNormalizar(unittest.TestCase):
    def test_colapsa_espacios_y_saltos(self):
        self.assertEqual(textos._normalizar("hola   mundo\n\ny  más"), "hola mundo y más")

    def test_recorta_extremos(self):
        self.assertEqual(textos._normalizar("  hola  "), "hola")

    def test_cadena_vacia(self):
        self.assertEqual(textos._normalizar("   \n\t "), "")


class TestTrocearTexto(unittest.TestCase):
    def test_texto_vacio_devuelve_lista_vacia(self):
        self.assertEqual(textos.trocear_texto(""), [])
        self.assertEqual(textos.trocear_texto("    \n  "), [])

    def test_frase_corta_un_solo_fragmento(self):
        self.assertEqual(textos.trocear_texto("Hola mundo."), ["Hola mundo."])

    def test_agrupa_frases_hasta_el_maximo(self):
        texto = "Uno. Dos. Tres."
        self.assertEqual(textos.trocear_texto(texto, maximo=240), ["Uno. Dos. Tres."])

    def test_separa_cuando_excede_el_maximo(self):
        texto = "Primera frase larga. Segunda frase larga."
        fragmentos = textos.trocear_texto(texto, maximo=22)
        self.assertEqual(len(fragmentos), 2)
        self.assertTrue(all(len(f) <= 22 for f in fragmentos))

    def test_ningun_fragmento_excede_el_maximo(self):
        # Una sola "frase" sin puntuación más larga que el máximo: se parte por palabras.
        texto = "palabra " * 50
        fragmentos = textos.trocear_texto(texto, maximo=30)
        self.assertTrue(fragmentos)
        self.assertTrue(all(len(f) <= 30 for f in fragmentos))

    def test_conserva_acentos_y_enie(self):
        fragmentos = textos.trocear_texto("El niño comió ñoquis con cariño.")
        self.assertEqual(fragmentos, ["El niño comió ñoquis con cariño."])


class TestCitaAleatoria(unittest.TestCase):
    def test_evita_repetir_la_ultima(self):
        citas = [{"texto": "a"}, {"texto": "b"}]
        # Con dos citas, evitando "a", siempre debe salir "b".
        for _ in range(20):
            self.assertEqual(textos.cita_aleatoria(citas, evitar_texto="a")["texto"], "b")

    def test_una_sola_cita_se_devuelve_aunque_se_evite(self):
        citas = [{"texto": "a"}]
        self.assertEqual(textos.cita_aleatoria(citas, evitar_texto="a")["texto"], "a")

    def test_devuelve_elemento_de_la_lista(self):
        citas = [{"texto": "a"}, {"texto": "b"}, {"texto": "c"}]
        self.assertIn(textos.cita_aleatoria(citas), citas)


if __name__ == "__main__":
    unittest.main()
