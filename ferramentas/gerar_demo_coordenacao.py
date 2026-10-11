"""Gera dois casos de demonstração sintéticos.

1. dados/demo/campanha_coordenada.csv (+ _verdade.json)
   Uma campanha fictícia contra o Banco Aurora: 3 células de contas que
   repetem links de golpe e textos quase iguais em rajadas, misturadas com
   contas orgânicas que falam do mesmo assunto em horários espalhados.
   Inclui uma armadilha honesta: um grupo de imprensa que também compartilha
   o mesmo link oficial em sequência (coordenação legítima).
   Formato de colunas igual ao do coordination-network-toolkit.

2. dados/demo/geo_previsoes.jsonl
   Previsões simuladas de um geolocalizador (top-5 com probabilidade) para
   fotos fictícias com GPS verdadeiro em cidades brasileiras. O modelo
   simulado é superconfiante em paisagens genéricas, para exercitar a
   auditoria de calibração por distância sem GPU.

Uso:  python ferramentas/gerar_demo_coordenacao.py
"""

import csv
import json
import os
import random

SEMENTE = 3407
PASTA = os.path.join(os.path.dirname(__file__), "..", "dados", "demo")
INICIO = 1_790_000_000  # instante fixo, apenas para reprodutibilidade

GOLPE = ["https://aurora-estorno.example/login", "https://aurora-premios.example/resgate", "https://bit.example/aur0ra"]
OFICIAL = "https://aurora.example/comunicado"
NOTICIAS = ["https://jornal-a.example/economia/aurora", "https://portal-b.example/aurora-instabilidade"]
FRASES_GOLPE = [
    "Clientes do Banco Aurora: seu estorno foi liberado, confirme seus dados no link agora",
    "Atenção clientes Banco Aurora seu estorno foi liberado confirme os dados no link hoje",
    "URGENTE Banco Aurora liberou prêmio para correntistas, resgate no link antes que expire",
    "Banco Aurora liberou prêmio para correntistas resgate no link antes que expire hoje",
]
FRASES_ORGANICAS = [
    "Alguém mais com o app do Aurora fora do ar?", "Fui no caixa do Aurora hoje, fila enorme",
    "O atendimento do Aurora resolveu meu problema", "Recebi uma mensagem estranha dizendo ser do Aurora, cuidado",
    "Vale a pena a conta do Aurora?", "Aurora subiu a tarifa de novo", "Minha fatura do Aurora veio errada",
]


def gerar_campanha(r):
    linhas, verdade, mid = [], {}, 0

    def post(uid, user, ts, texto, urls=(), repost=""):
        nonlocal mid
        mid += 1
        linhas.append({"message_id": f"m{mid}", "user_id": uid, "username": user, "repost_id": repost,
                       "reply_id": "", "message": texto, "timestamp": ts, "urls": " ".join(urls)})
        return f"m{mid}"

    # 3 células coordenadas
    for c in range(3):
        contas = [(f"c{c}_{i}", f"aurora_alerta{c}{i}{r.randint(10, 99)}") for i in range(r.randint(5, 8))]
        for uid, _ in contas:
            verdade[uid] = f"celula_{c}"
        for onda in range(6):
            base = INICIO + c * 50_000 + onda * 7_200 + r.randint(0, 600)
            link = r.choice(GOLPE)
            frase = r.choice(FRASES_GOLPE)
            primeiro = None
            for uid, user in contas:
                if r.random() < 0.8:
                    mid_ = post(uid, user, base + r.randint(0, 45), frase, [link])
                    primeiro = primeiro or mid_
            for uid, user in contas:
                if primeiro and r.random() < 0.4:
                    post(uid, user, base + r.randint(46, 110), "", [], repost=primeiro)

    # imprensa: compartilha o mesmo link oficial em sequência (coordenação legítima)
    imprensa = [(f"imp_{i}", f"redacao_{n}") for i, n in enumerate(["jornal_a", "portal_b", "radio_c"])]
    for uid, _ in imprensa:
        verdade[uid] = None
    for onda in range(3):
        base = INICIO + 20_000 + onda * 30_000
        for uid, user in imprensa:
            post(uid, user, base + r.randint(0, 50), f"Banco Aurora divulga comunicado oficial sobre golpes ({onda + 1})", [OFICIAL])

    # contas orgânicas
    for i in range(60):
        uid, user = f"org_{i}", f"pessoa{i}_{r.randint(100, 999)}"
        verdade[uid] = None
        for _ in range(r.randint(1, 4)):
            urls = [r.choice(NOTICIAS)] if r.random() < 0.3 else []
            post(uid, user, INICIO + r.randint(0, 200_000), r.choice(FRASES_ORGANICAS), urls)

    linhas.sort(key=lambda l: l["timestamp"])
    return linhas, verdade


CIDADES = {
    "Belo Horizonte": (-19.9167, -43.9345), "São Paulo": (-23.5505, -46.6333), "Rio de Janeiro": (-22.9068, -43.1729),
    "Recife": (-8.0476, -34.8770), "Salvador": (-12.9777, -38.5016), "Manaus": (-3.1190, -60.0217),
    "Porto Alegre": (-30.0346, -51.2177), "Brasília": (-15.7939, -47.8828), "Curitiba": (-25.4284, -49.2733),
    "Belém": (-1.4558, -48.4902), "Fortaleza": (-3.7319, -38.5267), "Florianópolis": (-27.5954, -48.5480),
}
CENAS = {"marco_urbano": 0.85, "rua_comum": 0.55, "natureza": 0.30, "interior": 0.15}


def gerar_geo(r):
    saida = []
    nomes = list(CIDADES)
    for i in range(240):
        cidade = r.choice(nomes)
        cena = r.choice(list(CENAS))
        lat, lon = CIDADES[cidade]
        verdade = (lat + r.uniform(-0.05, 0.05), lon + r.uniform(-0.05, 0.05))
        acerta = r.random() < CENAS[cena]
        centro = (verdade if acerta else CIDADES[r.choice([c for c in nomes if c != cidade])])
        # o top-5 costuma se espalhar quando o modelo erra, mas não sempre:
        # há erros confiantes (top-5 agrupado no lugar errado) e acertos hesitantes
        disperso = r.random() < (0.25 if acerta else 0.70)
        top = []
        for k in range(5):
            espalhamento = 0.05 if k == 0 else (4.0 if disperso else 0.3)
            top.append((round(centro[0] + r.uniform(-espalhamento, espalhamento), 5),
                        round(centro[1] + r.uniform(-espalhamento, espalhamento), 5)))
        # superconfiança: o modelo diz ~0.5-0.8 mesmo em natureza e interiores
        p1 = r.uniform(0.45, 0.85)
        resto = [r.random() for _ in range(4)]
        resto = [x / sum(resto) * (1 - p1) for x in resto]
        saida.append({"id": f"foto_{i:03d}", "cena": cena, "cidade_real": cidade,
                      "verdade": [round(verdade[0], 5), round(verdade[1], 5)],
                      "topk": [list(t) for t in top], "probs": [round(p1, 4)] + [round(x, 4) for x in resto]})
    return saida


def main():
    r = random.Random(SEMENTE)
    os.makedirs(PASTA, exist_ok=True)
    linhas, verdade = gerar_campanha(r)
    csv_path = os.path.join(PASTA, "campanha_coordenada.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    with open(os.path.join(PASTA, "campanha_coordenada_verdade.json"), "w", encoding="utf-8") as f:
        json.dump(verdade, f, ensure_ascii=False, indent=1)
    print(f"{len(linhas)} mensagens de {len(verdade)} contas em {os.path.normpath(csv_path)}")

    geo = gerar_geo(r)
    with open(os.path.join(PASTA, "geo_previsoes.jsonl"), "w", encoding="utf-8") as f:
        for g in geo:
            f.write(json.dumps(g, ensure_ascii=False) + "\n")
    print(f"{len(geo)} previsões de geolocalização em dados/demo/geo_previsoes.jsonl")


if __name__ == "__main__":
    main()
