"""Testes do núcleo stdlib. Rodar:  python -m unittest discover -s testes -v"""

import json
import os
import random
import sys
import tempfile
import unittest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)

from osintia import auditoria, calibracao, custodia, dados, esquemas, extracao, roteamento  # noqa: E402

DEMO = os.path.join(RAIZ, "dados", "demo", "triagem_perfis.jsonl")


class TestCalibracao(unittest.TestCase):
    def setUp(self):
        r = random.Random(1)
        self.probs, self.rotulos = [], []
        # modelo superconfiante: diz 95% mas acerta ~70%
        for _ in range(2000):
            certo = r.random() < 0.70
            verdade = r.choice("abc")
            previsto = verdade if certo else r.choice([x for x in "abc" if x != verdade])
            p = {x: 0.025 for x in "abc"}
            p[previsto] = 0.95
            self.probs.append(p)
            self.rotulos.append(verdade)

    def test_ece_detecta_superconfianca(self):
        self.assertGreater(calibracao.ece(self.probs, self.rotulos), 0.2)

    def test_temperatura_reduz_ece(self):
        t = calibracao.ajustar_temperatura(self.probs, self.rotulos)
        self.assertGreater(t, 1.0)
        ajustado = [calibracao.aplicar_temperatura(p, t) for p in self.probs]
        self.assertLess(calibracao.ece(ajustado, self.rotulos), 0.05)
        self.assertAlmostEqual(calibracao.acuracia(ajustado, self.rotulos), calibracao.acuracia(self.probs, self.rotulos))

    def test_temperatura_preserva_soma(self):
        p = calibracao.aplicar_temperatura({"a": 0.7, "b": 0.2, "c": 0.1}, 2.0)
        self.assertAlmostEqual(sum(p.values()), 1.0)

    def test_brier_perfeito(self):
        self.assertEqual(calibracao.brier([{"a": 1.0, "b": 0.0}], ["a"]), 0.0)


class TestAuditoria(unittest.TestCase):
    def test_concordancia_e_kappa(self):
        self.assertEqual(auditoria.concordancia("aab", "aab"), 1.0)
        self.assertAlmostEqual(auditoria.kappa_cohen("aabb", "aabb"), 1.0)
        self.assertLess(auditoria.kappa_cohen("abab", "baba"), 0)

    def test_tamanho_diferente(self):
        with self.assertRaises(ValueError):
            auditoria.concordancia("ab", "a")

    def test_aluno_que_decora_professor_dispara_alerta(self):
        linhas = dados.carregar_jsonl(DEMO)
        gold = dados.rotulos(linhas, "perfil")
        humano = [l["rotulo_humano"]["perfil"] for l in linhas]
        extra = [l["amostra_professor_extra"]["perfil"] for l in linhas]
        teto = auditoria.teto_do_professor([extra], gold)
        aluno = list(gold)  # aluno que copiou o gabarito
        self.assertTrue(auditoria.alerta_de_decoracao(auditoria.concordancia(aluno, gold), teto))
        lacuna = auditoria.lacuna_humana(aluno, gold, humano)
        self.assertGreater(lacuna["lacuna"], 0.1)
        self.assertTrue(auditoria.erros_herdados(aluno, gold, humano))

    def test_matriz(self):
        texto = auditoria.imprimir_matriz(["a", "b"], ["a", "a"])
        self.assertIn("a", texto)


class TestRoteamento(unittest.TestCase):
    def test_limiar(self):
        self.assertEqual(roteamento.rotear({"x": 0.81, "y": 0.19}), "x")
        self.assertEqual(roteamento.rotear({"x": 0.6, "y": 0.4}), roteamento.REVISAO)

    def test_limiar_por_opcao(self):
        p = {"descartar": 0.85, "bloquear": 0.15}
        self.assertEqual(roteamento.rotear(p, limiares={"descartar": 0.9}), roteamento.REVISAO)

    def test_varredura(self):
        res = roteamento.varrer_limiares([{"a": 0.9, "b": 0.1}, {"a": 0.55, "b": 0.45}], ["a", "b"])
        self.assertEqual(res[0]["cobertura"], 1.0)
        self.assertEqual(res[-1]["cobertura"], 0.0)

    def test_almirantado(self):
        self.assertEqual(roteamento.codigo_almirantado("B", 2), "B2")
        with self.assertRaises(ValueError):
            roteamento.codigo_almirantado("G", 2)


class TestEsquemas(unittest.TestCase):
    def test_catalogo_valido(self):
        for nome, esquema in esquemas.CATALOGO.items():
            erros, _ = esquemas.validar(esquema)
            self.assertEqual(erros, [], nome)

    def test_limites(self):
        grande = {"q": {"type": "choice", "instructions": "x", "criteria": {str(i): "d" for i in range(30)}}}
        erros, avisos = esquemas.validar(grande)
        self.assertEqual(erros, [])
        self.assertTrue(avisos)
        niveis = {"q": {"type": "score", "instructions": "x", "criteria": list("abcdefghijk")}}
        self.assertTrue(esquemas.validar(niveis)[0])

    def test_opcoes(self):
        self.assertEqual(esquemas.opcoes({"type": "noul"}), [True, False])


class TestDados(unittest.TestCase):
    def test_gold_suave(self):
        g = dados.gold_de_amostras(["a", "a", "b"], ["a", "b", "c"])
        self.assertEqual(g["label"], "a")
        self.assertAlmostEqual(g["probabilities"]["a"], 2 / 3)
        self.assertAlmostEqual(g["confidence"], 0.5)

    def test_demo_formato(self):
        linha = dados.carregar_jsonl(DEMO)[0]
        self.assertIsInstance(linha["questions"], str)
        gold = json.loads(linha["gold"])
        self.assertEqual(set(gold), {"perfil", "acao"})
        self.assertAlmostEqual(sum(gold["perfil"]["probabilities"].values()), 1.0)

    def test_holdout_reprodutivel(self):
        a = dados.dividir_holdout(list(range(100)))
        b = dados.dividir_holdout(list(range(100)))
        self.assertEqual(a, b)
        self.assertEqual(len(a[1]), 20)


class TestCustodia(unittest.TestCase):
    def test_cadeia_integra_e_adulterada(self):
        with tempfile.TemporaryDirectory() as d:
            arq = os.path.join(d, "evidencia.txt")
            with open(arq, "w") as f:
                f.write("print da página")
            man = os.path.join(d, "manifesto.jsonl")
            custodia.registrar(man, "coleta", arq, {"fonte": "exemplo"})
            custodia.registrar(man, "inferencia", detalhes={"modelo": "teste"})
            self.assertEqual(custodia.verificar(man), [])
            with open(arq, "a") as f:
                f.write(" editado")
            self.assertTrue(any("modificado" in p for p in custodia.verificar(man)))

    def test_linha_editada(self):
        with tempfile.TemporaryDirectory() as d:
            man = os.path.join(d, "m.jsonl")
            custodia.registrar(man, "a")
            custodia.registrar(man, "b")
            with open(man) as f:
                linhas = f.readlines()
            linhas[0] = linhas[0].replace('"a"', '"x"')
            with open(man, "w") as f:
                f.writelines(linhas)
            self.assertTrue(custodia.verificar(man))


class TestExtracao(unittest.TestCase):
    def test_documentos(self):
        self.assertTrue(extracao.cpf_valido("529.982.247-25"))
        self.assertFalse(extracao.cpf_valido("529.982.247-24"))
        self.assertFalse(extracao.cpf_valido("111.111.111-11"))
        self.assertTrue(extracao.cnpj_valido("11.222.333/0001-81"))
        self.assertFalse(extracao.cnpj_valido("11.222.333/0001-80"))

    def test_extrair_texto(self):
        t = "Fale com @suporte_aurora no (31) 99999-0000 ou golpe@aurora.example, CPF 529.982.247-25, IP 8.8.8.8"
        tipos = {a["tipo"] for a in extracao.extrair(t)}
        self.assertTrue({"handle", "telefone", "email", "cpf", "ip"} <= tipos)

    def test_mascarar(self):
        m = extracao.mascarar("CPF 529.982.247-25 e e-mail a@b.com")
        self.assertNotIn("529", m)
        self.assertIn("[CPF]", m)
        self.assertIn("[EMAIL]", m)

    def test_ip_publico(self):
        self.assertTrue(extracao.ip_publico("8.8.8.8"))
        self.assertFalse(extracao.ip_publico("192.168.0.1"))


if __name__ == "__main__":
    unittest.main()
