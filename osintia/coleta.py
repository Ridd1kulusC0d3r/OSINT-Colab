"""Coleta em fontes abertas — só stdlib.

Três fontes públicas, sem chave de API:
    - crt.sh: logs de Certificate Transparency. Domínios imitadores aparecem
      aqui quando o certificado HTTPS é emitido, muitas vezes antes do golpe.
    - Wayback Machine (CDX): capturas históricas de uma URL.
    - IDs de analytics (UA-, G-, GTM-, pixel) no HTML arquivado: sites do
      mesmo dono costumam reutilizar o mesmo ID (técnica popularizada pela
      Bellingcat no notebook Wayback Google Analytics).

Mais um gerador de variantes de username/domínio (a ideia do SÓSIA).

As funções de rede respeitam um intervalo entre requisições. Use com
moderação, em fontes públicas e com finalidade legítima.
"""

import json
import re
import time
import urllib.parse
import urllib.request

AGENTE = "OSINTIA/1.1 (+https://github.com/Ridd1kulusC0d3r/OSINTIA)"
INTERVALO_S = 1.5
_ultima = [0.0]

RE_ANALYTICS = {
    "google_ua": re.compile(r"\bUA-\d{4,10}-\d{1,4}\b"),
    "google_g4": re.compile(r"\bG-[A-Z0-9]{8,12}\b"),
    "google_tag_manager": re.compile(r"\bGTM-[A-Z0-9]{5,9}\b"),
    "google_ads": re.compile(r"\bAW-\d{8,12}\b"),
    "adsense": re.compile(r"\bca-pub-\d{10,20}\b"),
    "facebook_pixel": re.compile(r"fbq\(\s*['\"]init['\"]\s*,\s*['\"](\d{10,20})['\"]"),
}

HOMOGLIFOS = {"o": "0", "i": "1", "l": "1", "e": "3", "a": "4", "s": "5", "b": "8", "g": "9"}
SUFIXOS = ["oficial", "sac", "suporte", "atendimento", "br", "app", "help", "online", "pay"]


def obter(url, timeout=60):
    """GET com User-Agent e intervalo mínimo entre chamadas."""
    espera = INTERVALO_S - (time.time() - _ultima[0])
    if espera > 0:
        time.sleep(espera)
    req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        dados = r.read()
    _ultima[0] = time.time()
    return dados.decode("utf-8", errors="replace")


# ------------------------------------------------------------- crt.sh

def url_crtsh(termo):
    return "https://crt.sh/?" + urllib.parse.urlencode({"q": termo, "output": "json"})


def parse_crtsh(texto):
    """Lista de {dominio, emissor, inicio, fim} sem duplicatas de domínio."""
    vistos, saida = set(), []
    for c in json.loads(texto or "[]"):
        for nome in c.get("name_value", "").split("\n"):
            nome = nome.strip().lower().lstrip("*.")
            if nome and nome not in vistos:
                vistos.add(nome)
                saida.append({"dominio": nome, "emissor": c.get("issuer_name", ""),
                              "inicio": c.get("not_before", ""), "fim": c.get("not_after", "")})
    return saida


def crtsh(termo):
    """Ex.: crtsh('%aurora%') — domínios com 'aurora' em certificados públicos."""
    return parse_crtsh(obter(url_crtsh(termo)))


# ------------------------------------------------------------- Wayback

def url_cdx(url, de=None, ate=None, limite=200):
    p = {"url": url, "output": "json", "fl": "timestamp,original,statuscode,digest",
         "collapse": "digest", "limit": str(limite)}
    if de:
        p["from"] = de
    if ate:
        p["to"] = ate
    return "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(p)


def parse_cdx(texto):
    linhas = json.loads(texto or "[]")
    if not linhas:
        return []
    cab = linhas[0]
    return [dict(zip(cab, l)) for l in linhas[1:]]


def capturas(url, **kw):
    return parse_cdx(obter(url_cdx(url, **kw)))


def url_arquivada(timestamp, original):
    """O sufixo id_ devolve o HTML original, sem a barra do Wayback."""
    return f"https://web.archive.org/web/{timestamp}id_/{original}"


def ids_analytics(html):
    """{tipo: [ids]} encontrados no HTML."""
    achados = {}
    for tipo, rx in RE_ANALYTICS.items():
        m = rx.findall(html)
        if m:
            achados[tipo] = sorted(set(m))
    return achados


def historico_analytics(url, max_capturas=20, **kw):
    """Linha do tempo de IDs de analytics de um site, a partir do Wayback."""
    linha = []
    for c in capturas(url, **kw)[:max_capturas]:
        try:
            ids = ids_analytics(obter(url_arquivada(c["timestamp"], c["original"])))
        except Exception as e:  # captura quebrada ou fora do ar: registra e segue
            ids = {"erro": [type(e).__name__]}
        linha.append({"timestamp": c["timestamp"], "url": c["original"], "ids": ids})
    return linha


def ids_compartilhados(historicos):
    """historicos: {site: linha_do_tempo}. Devolve {id: [sites]} para IDs em 2+ sites."""
    por_id = {}
    for site, linha in historicos.items():
        for cap in linha:
            for tipo, ids in cap["ids"].items():
                if tipo == "erro":
                    continue
                for i in ids:
                    por_id.setdefault(i, set()).add(site)
    return {i: sorted(s) for i, s in por_id.items() if len(s) > 1}


# ------------------------------------------------------------- variantes

def variantes(nome, sufixos=SUFIXOS, max_itens=200):
    """Variantes plausíveis de imitação: homóglifos, letra dobrada/omitida, troca, sufixos, separadores."""
    nome = nome.lower()
    v = set()
    for i, ch in enumerate(nome):
        if ch in HOMOGLIFOS:
            v.add(nome[:i] + HOMOGLIFOS[ch] + nome[i + 1:])
        v.add(nome[:i] + ch + nome[i:])          # letra dobrada
        v.add(nome[:i] + nome[i + 1:])           # letra omitida
        if i < len(nome) - 1:                    # letras trocadas
            v.add(nome[:i] + nome[i + 1] + nome[i] + nome[i + 2:])
        if 0 < i < len(nome):
            v.add(nome[:i] + "." + nome[i:])
            v.add(nome[:i] + "_" + nome[i:])
    for s in sufixos:
        v.update({f"{nome}{s}", f"{nome}_{s}", f"{nome}.{s}", f"{s}_{nome}", f"{s}{nome}"})
    v.discard(nome)
    v = {x for x in v if len(x) >= 3}
    return sorted(v, key=lambda x: (abs(len(x) - len(nome)), x))[:max_itens]


def ler_ndjson(caminho):
    """Lê relatórios em NDJSON (um JSON por linha), formato usado por ferramentas como Maigret."""
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]
