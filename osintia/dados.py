"""Dados no formato de linhas de decisão: state / questions / gold.

Cada linha (igual ao dataset LocalLLaMA/typed-decisions usado pela Unsloth):
    state     -> texto de entrada (o que o modelo lê)
    questions -> JSON (texto) com as perguntas, ver osintia.esquemas
    gold      -> JSON (texto) com a resposta de cada pergunta:
                 {"pergunta": {"type": "choice", "label": "x",
                               "probabilities": {...}, "confidence": 0.8}}

O gold pode ser "suave": em vez de 100% numa opção, a média de várias
amostras do professor. Por isso guardamos as probabilidades.
"""

import json
import random
from collections import Counter


def carregar_jsonl(caminho):
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def salvar_jsonl(linhas, caminho):
    with open(caminho, "w", encoding="utf-8") as f:
        for linha in linhas:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")


def gold_de_amostras(amostras, opcoes):
    """Gold suave a partir de várias respostas (ex.: 3 amostras do professor).

    Devolve {"label", "probabilities", "confidence"}. A confiança segue a ideia
    da Laya: perto de 1 quando uma opção se destaca, perto de 0 quando está
    espalhado. Aqui: (p_max - 1/k) / (1 - 1/k).
    """
    contagem = Counter(amostras)
    n, k = len(amostras), len(opcoes)
    probs = {o: contagem.get(o, 0) / n for o in opcoes}
    label = max(probs, key=probs.get)
    confianca = (probs[label] - 1 / k) / (1 - 1 / k) if k > 1 else 1.0
    return {"label": label, "probabilities": probs, "confidence": round(confianca, 6)}


def montar_linha(id_, state, perguntas, respostas, tipos=None):
    """respostas: {pergunta: lista_de_amostras}. Só choice neste helper."""
    gold = {}
    for nome, amostras in respostas.items():
        g = gold_de_amostras(amostras, list(perguntas[nome]["criteria"]))
        g["type"] = (tipos or {}).get(nome, perguntas[nome]["type"])
        gold[nome] = g
    return {
        "id": id_,
        "state": state,
        "questions": json.dumps(perguntas, ensure_ascii=False),
        "gold": json.dumps(gold, ensure_ascii=False),
    }


def rotulos(linhas, pergunta, campo="gold"):
    """Extrai a lista de rótulos de uma pergunta a partir das linhas."""
    saida = []
    for l in linhas:
        g = l[campo]
        g = json.loads(g) if isinstance(g, str) else g
        saida.append(g[pergunta]["label"] if isinstance(g[pergunta], dict) else g[pergunta])
    return saida


def dividir_holdout(linhas, fracao=0.2, semente=3407):
    """Separa treino e holdout de forma reprodutível."""
    copia = list(linhas)
    random.Random(semente).shuffle(copia)
    corte = int(len(copia) * (1 - fracao))
    return copia[:corte], copia[corte:]
