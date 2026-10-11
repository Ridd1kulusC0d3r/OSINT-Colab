"""Cadeia de custódia com manifesto SHA-256 encadeado.

Cada evento (coleta, inferência, decisão) vira uma linha JSONL que guarda:
    - o hash SHA-256 do artefato (arquivo de entrada ou saída), se houver
    - o hash da linha anterior

Se alguém editar uma linha antiga ou trocar um arquivo, verificar() aponta
exatamente onde a cadeia quebrou. Útil para laudos e relatórios periciais.
"""

import hashlib
import json
from datetime import datetime, timezone

GENESE = "0" * 64


def sha256_arquivo(caminho, bloco=1 << 20):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for parte in iter(lambda: f.read(bloco), b""):
            h.update(parte)
    return h.hexdigest()


def sha256_texto(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _ultima_linha(caminho):
    try:
        with open(caminho, encoding="utf-8") as f:
            linhas = [l for l in f if l.strip()]
    except FileNotFoundError:
        return None
    return json.loads(linhas[-1]) if linhas else None


def registrar(manifesto, acao, artefato=None, detalhes=None, agora=None):
    """Acrescenta um evento ao manifesto e devolve o registro gravado."""
    anterior = _ultima_linha(manifesto)
    registro = {
        "seq": (anterior["seq"] + 1) if anterior else 1,
        "quando": agora or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "acao": acao,
        "artefato": artefato,
        "sha256_artefato": sha256_arquivo(artefato) if artefato else None,
        "detalhes": detalhes or {},
        "hash_anterior": anterior["hash"] if anterior else GENESE,
    }
    registro["hash"] = sha256_texto(json.dumps(registro, sort_keys=True, ensure_ascii=False))
    with open(manifesto, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def verificar(manifesto, checar_arquivos=True):
    """Devolve lista de problemas. Lista vazia = cadeia íntegra."""
    problemas = []
    esperado = GENESE
    with open(manifesto, encoding="utf-8") as f:
        for n, linha in enumerate((l for l in f if l.strip()), start=1):
            r = json.loads(linha)
            if r["hash_anterior"] != esperado:
                problemas.append(f"linha {n}: elo quebrado com a linha anterior")
            corpo = {k: v for k, v in r.items() if k != "hash"}
            if sha256_texto(json.dumps(corpo, sort_keys=True, ensure_ascii=False)) != r["hash"]:
                problemas.append(f"linha {n}: conteúdo alterado")
            if checar_arquivos and r.get("artefato"):
                try:
                    if sha256_arquivo(r["artefato"]) != r["sha256_artefato"]:
                        problemas.append(f"linha {n}: arquivo {r['artefato']} foi modificado")
                except FileNotFoundError:
                    problemas.append(f"linha {n}: arquivo {r['artefato']} não encontrado")
            esperado = r["hash"]
    return problemas
