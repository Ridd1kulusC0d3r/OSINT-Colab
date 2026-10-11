"""Detecção de comportamento coordenado — só stdlib.

Inspirado em dois trabalhos abertos:
    - coordination-network-toolkit (QUT, MIT): co-link, co-texto e co-repost
      dentro de uma janela de tempo, com o mesmo formato de CSV;
    - Phantomatics: fundir vários sinais num grafo e NUNCA atribuir
      automaticamente quem está por trás das contas.

Entrada: lista de mensagens (dicionários) com as colunas do toolkit:
    message_id, user_id, username, repost_id, reply_id, message, timestamp, urls
    timestamp em segundos (int) ou ISO 8601; urls separadas por espaço.

Saída: grafo de contas (arestas com peso por sinal) e grupos candidatos.
Um grupo é uma PISTA de coordenação, não um veredito. Jornais, campanhas de
marketing e movimentos sociais também coordenam.
"""

import csv
import re
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from urllib.parse import urlparse

AVISO = (
    "Grupos indicam coordenação suspeita, não autoria nem má-fé. "
    "Atribuição a pessoas ou organizações exige análise humana e evidência independente."
)

PESOS_PADRAO = {"co_link": 1.0, "co_texto": 1.0, "co_repost": 1.0, "co_dominio": 0.5}


def ler_csv(caminho):
    with open(caminho, encoding="utf-8", newline="") as f:
        return [normalizar(l) for l in csv.DictReader(f)]


def normalizar(msg):
    m = dict(msg)
    ts = m.get("timestamp", 0)
    if isinstance(ts, str):
        ts = int(ts) if ts.isdigit() else int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())
    m["timestamp"] = int(ts)
    urls = m.get("urls") or ""
    m["urls"] = urls.split() if isinstance(urls, str) else list(urls)
    return m


def dominio(url):
    host = urlparse(url if "//" in url else "//" + url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def telhas(texto, n=3):
    """Conjunto de n-gramas de palavras (shingles) para similaridade de texto."""
    palavras = re.findall(r"\w+", texto.lower())
    if len(palavras) < n:
        return {" ".join(palavras)} if palavras else set()
    return {" ".join(palavras[i:i + n]) for i in range(len(palavras) - n + 1)}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def _pares_na_janela(itens, janela):
    """itens: lista de (timestamp, usuario). Pares de usuários distintos dentro da janela."""
    itens = sorted(itens)
    for i, (t1, u1) in enumerate(itens):
        for t2, u2 in itens[i + 1:]:
            if t2 - t1 > janela:
                break
            if u1 != u2:
                yield tuple(sorted((u1, u2)))


def sinais(mensagens, janela=60, limiar_texto=0.7, janela_texto=3600):
    """Conta, por par de contas, quantas vezes cada sinal de coordenação apareceu."""
    contagem = defaultdict(lambda: defaultdict(int))

    por_url, por_dominio, por_repost = defaultdict(list), defaultdict(list), defaultdict(list)
    for m in mensagens:
        for u in m["urls"]:
            por_url[u].append((m["timestamp"], m["user_id"]))
            por_dominio[dominio(u)].append((m["timestamp"], m["user_id"]))
        if m.get("repost_id"):
            por_repost[m["repost_id"]].append((m["timestamp"], m["user_id"]))

    for grupo, nome in ((por_url, "co_link"), (por_dominio, "co_dominio"), (por_repost, "co_repost")):
        for itens in grupo.values():
            for par in set(_pares_na_janela(itens, janela)):
                contagem[par][nome] += 1

    originais = [m for m in mensagens if m.get("message") and not m.get("repost_id")]
    originais.sort(key=lambda m: m["timestamp"])
    cache = [telhas(m["message"]) for m in originais]
    for i, a in enumerate(originais):
        for j in range(i + 1, len(originais)):
            b = originais[j]
            if b["timestamp"] - a["timestamp"] > janela_texto:
                break
            if a["user_id"] != b["user_id"] and jaccard(cache[i], cache[j]) >= limiar_texto:
                contagem[tuple(sorted((a["user_id"], b["user_id"])))]["co_texto"] += 1

    return {par: dict(s) for par, s in contagem.items()}


def grafo(contagem, pesos=None, minimo=2.0):
    """Arestas com peso total >= minimo. Peso = soma(peso_do_sinal * ocorrências)."""
    pesos = pesos or PESOS_PADRAO
    arestas = {}
    for par, s in contagem.items():
        total = sum(pesos.get(k, 1.0) * v for k, v in s.items())
        if total >= minimo:
            arestas[par] = {"peso": round(total, 3), "sinais": s}
    return arestas


def grupos(arestas):
    """Componentes conexos (union-find). Devolve lista de conjuntos, maior primeiro."""
    pai = {}

    def raiz(x):
        pai.setdefault(x, x)
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    for a, b in arestas:
        pai[raiz(a)] = raiz(b)
    comp = defaultdict(set)
    for x in pai:
        comp[raiz(x)].add(x)
    return sorted(comp.values(), key=len, reverse=True)


def resumo_grupo(grupo, arestas, mensagens):
    """Evidência de um grupo: sinais somados, densidade e domínios mais compartilhados."""
    internas = {p: d for p, d in arestas.items() if p[0] in grupo and p[1] in grupo}
    n = len(grupo)
    possiveis = n * (n - 1) / 2
    sinais_total = defaultdict(int)
    for d in internas.values():
        for k, v in d["sinais"].items():
            sinais_total[k] += v
    doms = defaultdict(int)
    for m in mensagens:
        if m["user_id"] in grupo:
            for u in m["urls"]:
                doms[dominio(u)] += 1
    return {
        "contas": sorted(grupo),
        "tamanho": n,
        "densidade": round(len(internas) / possiveis, 3) if possiveis else 0.0,
        "sinais": dict(sinais_total),
        "dominios": sorted(doms.items(), key=lambda x: -x[1])[:5],
        "conclusao": "coordenação suspeita — requer análise humana",
        "atribuicao": None,
    }


def avaliar(grupos_encontrados, verdade):
    """Precisão e cobertura por conta. verdade: {user_id: id_campanha ou None}."""
    marcadas = set().union(*grupos_encontrados) if grupos_encontrados else set()
    coordenadas = {u for u, c in verdade.items() if c}
    vp = len(marcadas & coordenadas)
    return {
        "precisao": round(vp / len(marcadas), 4) if marcadas else 0.0,
        "cobertura": round(vp / len(coordenadas), 4) if coordenadas else 0.0,
        "marcadas": len(marcadas),
        "coordenadas_reais": len(coordenadas),
    }


def exportar_graphml(arestas, caminho):
    """GraphML simples (abre no Gephi), sem dependências."""
    nos = sorted({u for par in arestas for u in par})
    with open(caminho, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        f.write('  <key id="w" for="edge" attr.name="peso" attr.type="double"/>\n')
        f.write('  <graph edgedefault="undirected">\n')
        for n in nos:
            f.write(f'    <node id="{_xml(n)}"/>\n')
        for (a, b), d in arestas.items():
            f.write(f'    <edge source="{_xml(a)}" target="{_xml(b)}"><data key="w">{d["peso"]}</data></edge>\n')
        f.write("  </graph>\n</graphml>\n")


def _xml(s):
    return str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
