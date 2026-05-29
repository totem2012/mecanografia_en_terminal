"""Tests del resumen de estadísticas de la sesión."""

import unittest

from typing_trainer import estadisticas


def _r(ppm, precision=90.0, errores=0, fecha="2026-01-01T00:00:00"):
    return {"ppm": ppm, "precision": precision, "errores": errores, "fecha": fecha}


class TestResumen(unittest.TestCase):
    def test_sesion_vacia_devuelve_none(self):
        self.assertIsNone(estadisticas.resumen([]))

    def test_agregados_basicos(self):
        res = estadisticas.resumen([_r(40, 90), _r(60, 100), _r(50, 80)])
        self.assertEqual(res["total"], 3)
        self.assertEqual(res["mejor_ppm"], 60)
        self.assertEqual(res["ppm_promedio"], 50)
        self.assertEqual(res["mejor_precision"], 100)
        self.assertAlmostEqual(res["precision_promedio"], 90)

    def test_recientes_limitado_a_diez_y_en_orden_inverso(self):
        historial = [_r(i) for i in range(15)]
        res = estadisticas.resumen(historial)
        self.assertEqual(len(res["recientes"]), 10)
        # El más reciente (ppm=14) debe ir primero.
        self.assertEqual(res["recientes"][0]["ppm"], 14)
        self.assertEqual(res["recientes"][-1]["ppm"], 5)

    def test_no_expone_campos_no_usados(self):
        res = estadisticas.resumen([_r(40)])
        self.assertNotIn("ppm_promedio_reciente", res)


if __name__ == "__main__":
    unittest.main()
