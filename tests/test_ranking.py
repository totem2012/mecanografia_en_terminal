"""Tests del TOP 5: clasificación, inserción y orden, sobre un fichero temporal."""

import tempfile
import unittest
from pathlib import Path

from typing_trainer import ranking


class RankingTempMixin(unittest.TestCase):
    """Redirige la ruta del ranking a un fichero temporal por test."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._ruta_original = ranking.RUTA
        ranking.RUTA = Path(self._dir.name) / "ranking.json"

    def tearDown(self):
        ranking.RUTA = self._ruta_original
        self._dir.cleanup()

    @staticmethod
    def _res(ppm, precision=95.0):
        return {"ppm": ppm, "precision": precision, "fecha": "2026-01-01T00:00:00"}


class TestCalifica(RankingTempMixin):
    def test_califica_con_ranking_vacio(self):
        self.assertTrue(ranking.califica(1.0))

    def test_califica_si_hay_huecos(self):
        for ppm in (10, 20, 30):  # solo 3 marcas, TOPE=5
            ranking.agregar("x", self._res(ppm))
        self.assertTrue(ranking.califica(1.0))

    def test_no_califica_si_no_supera_la_minima(self):
        for ppm in (50, 40, 30, 20, 10):  # TOP lleno, mínima = 10
            ranking.agregar("x", self._res(ppm))
        self.assertFalse(ranking.califica(10))
        self.assertFalse(ranking.califica(5))
        self.assertTrue(ranking.califica(11))


class TestAgregar(RankingTempMixin):
    def test_devuelve_puesto_correcto(self):
        self.assertEqual(ranking.agregar("a", self._res(30)), 1)
        self.assertEqual(ranking.agregar("b", self._res(50)), 1)  # nuevo líder
        self.assertEqual(ranking.agregar("c", self._res(10)), 3)  # último

    def test_se_queda_con_las_cinco_mejores(self):
        for ppm in (10, 20, 30, 40, 50, 60, 70):
            ranking.agregar("x", self._res(ppm))
        tabla = ranking.cargar()
        self.assertEqual(len(tabla), 5)
        self.assertEqual([e["ppm"] for e in tabla], [70, 60, 50, 40, 30])

    def test_marca_que_no_entra_devuelve_none(self):
        for ppm in (50, 40, 30, 20, 10):
            ranking.agregar("x", self._res(ppm))
        self.assertIsNone(ranking.agregar("tarde", self._res(5)))

    def test_orden_estable_en_empates(self):
        ranking.agregar("primero", self._res(40))
        ranking.agregar("segundo", self._res(40))  # mismo PPM
        tabla = ranking.cargar()
        self.assertEqual(tabla[0]["nombre"], "primero")
        self.assertEqual(tabla[1]["nombre"], "segundo")


class TestCargar(RankingTempMixin):
    def test_sin_fichero_devuelve_vacio(self):
        self.assertEqual(ranking.cargar(), [])

    def test_json_corrupto_devuelve_vacio(self):
        ranking.RUTA.write_text("{ no es json valido", encoding="utf-8")
        self.assertEqual(ranking.cargar(), [])

    def test_ordena_de_mayor_a_menor(self):
        ranking.RUTA.write_text(
            '[{"nombre":"a","ppm":10},{"nombre":"b","ppm":30},{"nombre":"c","ppm":20}]',
            encoding="utf-8",
        )
        self.assertEqual([e["ppm"] for e in ranking.cargar()], [30, 20, 10])


if __name__ == "__main__":
    unittest.main()
