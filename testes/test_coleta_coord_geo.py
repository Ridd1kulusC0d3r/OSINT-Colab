"""Testes dos módulos coleta, coordenacao e geo (offline, sem rede)."""

import json
import os
import sys
import tempfile
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)

from osintia import coleta, coordenacao, dados, geo  # noqa: E402

DEMO = os.path.join(RAIZ, "dados", "demo")


class TestColeta(unittest.TestCase):
    def test_parse_crtsh(self):
        bruto = json.dumps([
            {"name_value": "aurora-estorno.example\n*.aurora-estorno.example", "issuer_name": "CA X", "not_before": "2026-10-01"},
            {"name_value": "aurora-estorno.example", "issuer_name": "CA Y"},
        ])
        r = coleta.parse_crtsh(bruto)
        self.assertEqual([x["dominio"] for x in r], ["aurora-estorno.example"])

    def test_urls(self):
        self.assertIn("output=json", coleta.url_crtsh("%aurora%"))
        self.assertIn("q=%25aurora%25", coleta.url_crtsh("%aurora%"))
        self.assertIn("collapse=digest", coleta.url_cdx("aurora.example", de="2024"))
        self.assertTrue(coleta.url_arquivada("20260101000000", "http://a.example/").endswith("id_/http://a.example/"))

    def test_parse_cdx(self):
        r = coleta.parse_cdx('[["timestamp","original"],["20260101","http://a.example/"]]')
        self.assertEqual(r, [{"timestamp": "20260101", "original": "http://a.example/"}])
        self.assertEqual(coleta.parse_cdx(""), [])

    def test_ids_analytics(self):
        html = "<script>ga('create','UA-1234567-2');gtag('config','G-ABCD1234EF');</script>" \
               "<!-- GTM-AB12CD --> fbq('init', '123456789012345'); ca-pub-1234567890123456"
        ids = coleta.ids_analytics(html)
        self.assertEqual(ids["google_ua"], ["UA-1234567-2"])
        self.assertEqual(ids["google_g4"], ["G-ABCD1234EF"])
        self.assertEqual(ids["google_tag_manager"], ["GTM-AB12CD"])
        self.assertEqual(ids["facebook_pixel"], ["123456789012345"])
        self.assertIn("adsense", ids)

    def test_ids_compartilhados(self):
        h = {
            "a.example": [{"ids": {"google_ua": ["UA-1-1"]}}],
            "b.example": [{"ids": {"google_ua": ["UA-1-1", "UA-2-1"]}}, {"ids": {"erro": ["URLError"]}}],
        }
        self.assertEqual(coleta.ids_compartilhados(h), {"UA-1-1": ["a.example", "b.example"]})

    def test_variantes(self):
        v = coleta.variantes("bancoaurora")
        for esperado in ("bancoaur0ra", "bancoaurora_oficial", "banco.aurora", "bancoauroraa", "bancoaurra"):
            self.assertIn(esperado, v)
        self.assertNotIn("bancoaurora", v)


class TestCoordenacao(unittest.TestCase):
    def setUp(self):
        self.msgs = coordenacao.ler_csv(os.path.join(DEMO, "campanha_coordenada.csv"))
        with open(os.path.join(DEMO, "campanha_coordenada_verdade.json"), encoding="utf-8") as f:
            self.verdade = json.load(f)

    def test_telhas_jaccard(self):
        a = coordenacao.telhas("seu estorno foi liberado confirme agora")
        self.assertEqual(coordenacao.jaccard(a, a), 1.0)
        self.assertEqual(coordenacao.jaccard(a, set()), 0.0)

    def test_dominio(self):
        self.assertEqual(coordenacao.dominio("https://www.Aurora.example/x"), "aurora.example")

    def test_detecta_celulas(self):
        g = coordenacao.grupos(coordenacao.grafo(coordenacao.sinais(self.msgs), minimo=3))
        res = coordenacao.avaliar(g, self.verdade)
        self.assertEqual(res["cobertura"], 1.0)
        self.assertGreaterEqual(res["precisao"], 0.8)

    def test_imprensa_e_coordenacao_legitima(self):
        g = coordenacao.grupos(coordenacao.grafo(coordenacao.sinais(self.msgs), minimo=3))
        imprensa = [x for x in g if any(u.startswith("imp_") for u in x)]
        self.assertTrue(imprensa, "a armadilha da imprensa deve aparecer como coordenação")

    def test_nunca_atribui(self):
        a = coordenacao.grafo(coordenacao.sinais(self.msgs), minimo=3)
        for grupo in coordenacao.grupos(a):
            r = coordenacao.resumo_grupo(grupo, a, self.msgs)
            self.assertIsNone(r["atribuicao"])
            self.assertIn("análise humana", r["conclusao"])

    def test_organicos_isolados_nao_formam_grupo(self):
        msgs = [coordenacao.normalizar({"message_id": str(i), "user_id": f"u{i}", "message": "oi", "timestamp": i * 10_000,
                                        "urls": "https://x.example"}) for i in range(5)]
        self.assertEqual(coordenacao.grupos(coordenacao.grafo(coordenacao.sinais(msgs))), [])

    def test_timestamp_iso(self):
        m = coordenacao.normalizar({"timestamp": "2026-10-11T12:00:00Z", "urls": ""})
        self.assertIsInstance(m["timestamp"], int)

    def test_graphml(self):
        a = coordenacao.grafo(coordenacao.sinais(self.msgs), minimo=3)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "g.graphml")
            coordenacao.exportar_graphml(a, p)
            with open(p, encoding="utf-8") as f:
                self.assertIn("<graphml", f.read())


class TestGeo(unittest.TestCase):
    def test_haversine(self):
        bh, sp = (-19.9167, -43.9345), (-23.5505, -46.6333)
        self.assertAlmostEqual(geo.haversine_km(bh, sp), 489, delta=5)
        self.assertEqual(geo.haversine_km(bh, bh), 0.0)

    def test_exif(self):
        self.assertAlmostEqual(geo.gps_exif_para_graus((19, 55, 0.12), "S"), -19.91670, places=4)
        self.assertGreater(geo.gps_exif_para_graus((43, 56, 4), "E"), 0)

    def test_acuracia_e_calibracao_demo(self):
        g = dados.carregar_jsonl(os.path.join(DEMO, "geo_previsoes.jsonl"))
        prev = [tuple(x["topk"][0]) for x in g]
        verd = [tuple(x["verdade"]) for x in g]
        acc = geo.acuracia_por_distancia(prev, verd)
        self.assertLessEqual(acc["rua"], acc["cidade"])
        self.assertLessEqual(acc["cidade"], acc["continente"])
        cal = geo.calibracao_distancia([x["probs"][0] for x in g], prev, verd, raio_km=25)
        self.assertGreater(cal["ece"], 0.05, "o modelo simulado é superconfiante")

    def test_dispersao(self):
        self.assertTrue(geo.concordancia_topk([(0, 0), (0, 0.1)])["estavel"])
        self.assertFalse(geo.concordancia_topk([(0, 0), (10, 10)])["estavel"])

    def test_kml(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.kml")
            geo.kml_pontos([{"nome": "x", "lat": -19.9, "lon": -43.9}], p)
            with open(p, encoding="utf-8") as f:
                self.assertIn("-43.9,-19.9,0", f.read())


if __name__ == "__main__":
    unittest.main()
