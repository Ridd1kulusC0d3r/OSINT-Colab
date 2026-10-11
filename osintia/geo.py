"""Geolocalização auditável — só stdlib.

Modelos como GeoCLIP devolvem as top-k coordenadas com probabilidade.
Este módulo mede se essa probabilidade merece confiança:

    - distância do grande círculo (haversine) entre previsão e verdade;
    - acurácia por limiar de distância, no padrão dos artigos
      (1 km rua, 25 km cidade, 200 km região, 750 km país, 2500 km continente);
    - calibração: quando o modelo diz 40% de probabilidade no top-1,
      a previsão cai a menos de X km cerca de 40% das vezes?

A verdade pode vir do GPS no EXIF das SUAS fotos originais. Assim você
audita o modelo no seu tipo de imagem antes de usá-lo num caso real.
"""

import math

RAIO_TERRA_KM = 6371.0088
LIMIARES_KM = {"rua": 1, "cidade": 25, "regiao": 200, "pais": 750, "continente": 2500}


def haversine_km(a, b):
    """Distância em km entre dois pontos (lat, lon) em graus."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(min(1.0, math.sqrt(h)))


def gps_exif_para_graus(valor, ref):
    """Converte o GPS do EXIF ((graus, min, seg), 'S'/'W') para grau decimal."""
    g, m, s = (float(x) for x in valor)
    dec = g + m / 60 + s / 3600
    return -dec if ref in ("S", "W") else dec


def acuracia_por_distancia(previsoes, verdades, limiares=None):
    """previsoes e verdades: listas de (lat, lon). Fração dentro de cada limiar."""
    limiares = limiares or LIMIARES_KM
    dist = [haversine_km(p, v) for p, v in zip(previsoes, verdades)]
    res = {nome: round(sum(d <= km for d in dist) / len(dist), 4) for nome, km in limiares.items()}
    ordenadas = sorted(dist)
    res["mediana_km"] = round(ordenadas[len(ordenadas) // 2], 1)
    return res


def calibracao_distancia(confiancas, previsoes, verdades, raio_km=750, n_faixas=5):
    """Tabela confiança × taxa de acerto dentro de raio_km, e ECE.

    confiancas: probabilidade do top-1 dada pelo modelo.
    """
    acertos = [haversine_km(p, v) <= raio_km for p, v in zip(previsoes, verdades)]
    faixas = [[] for _ in range(n_faixas)]
    for c, a in zip(confiancas, acertos):
        faixas[min(int(c * n_faixas), n_faixas - 1)].append((c, a))
    tabela, ece, n = [], 0.0, len(acertos)
    for i, f in enumerate(faixas):
        if not f:
            continue
        conf = sum(c for c, _ in f) / len(f)
        acc = sum(a for _, a in f) / len(f)
        ece += len(f) / n * abs(conf - acc)
        tabela.append({"faixa": f"{i / n_faixas:.1f}-{(i + 1) / n_faixas:.1f}", "n": len(f),
                       "confianca": round(conf, 3), "acerto": round(acc, 3)})
    return {"raio_km": raio_km, "ece": round(ece, 4), "tabela": tabela}


def concordancia_topk(previsoes_topk, raio_km=200):
    """Dispersão das top-k: se as k previsões estão longe umas das outras, o modelo não sabe.

    Devolve a maior distância entre o top-1 e as demais. Útil como sinal de
    revisão humana independente da probabilidade declarada.
    """
    top1 = previsoes_topk[0]
    maior = max((haversine_km(top1, p) for p in previsoes_topk[1:]), default=0.0)
    return {"dispersao_km": round(maior, 1), "estavel": maior <= raio_km}


def kml_pontos(pontos, caminho, nome="OSINTIA"):
    """pontos: lista de dicts {nome, lat, lon, descricao}. Abre no Google Earth."""
    with open(caminho, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document>\n')
        f.write(f"<name>{nome}</name>\n")
        for p in pontos:
            f.write(f"<Placemark><name>{p['nome']}</name><description>{p.get('descricao', '')}</description>"
                    f"<Point><coordinates>{p['lon']},{p['lat']},0</coordinates></Point></Placemark>\n")
        f.write("</Document></kml>\n")
