"""Calibração de probabilidades — só stdlib.

Ideia central: um modelo calibrado que diz 90% acerta cerca de 90% das vezes.
Mas atenção: "acerta" significa "concorda com o gabarito". Se o gabarito veio
de outro modelo, a calibração mede concordância com esse modelo, não verdade.
Veja osintia.auditoria para medir isso.

Formato usado em todo o módulo:
    probs  -> lista de dicionários {opcao: probabilidade}
    rotulos -> lista com a opção correta de cada item
"""

import math

EPS = 1e-12


def previsao(p):
    """Devolve (opcao_mais_provavel, probabilidade)."""
    opcao = max(p, key=p.get)
    return opcao, p[opcao]


def acuracia(probs, rotulos):
    acertos = sum(previsao(p)[0] == r for p, r in zip(probs, rotulos))
    return acertos / len(rotulos)


def ece(probs, rotulos, n_faixas=10):
    """Expected Calibration Error: distância média entre confiança e acerto.

    Agrupa as previsões em faixas de confiança e compara, em cada faixa,
    a confiança média com a taxa de acerto. Menor é melhor (0 = perfeito).
    """
    faixas = tabela_confiabilidade(probs, rotulos, n_faixas)
    total = len(rotulos)
    return sum(f["n"] / total * abs(f["confianca"] - f["acuracia"]) for f in faixas if f["n"])


def tabela_confiabilidade(probs, rotulos, n_faixas=10):
    """Uma linha por faixa de confiança: n, confiança média e acurácia."""
    grupos = [[] for _ in range(n_faixas)]
    for p, r in zip(probs, rotulos):
        opcao, conf = previsao(p)
        i = min(int(conf * n_faixas), n_faixas - 1)
        grupos[i].append((conf, opcao == r))
    tabela = []
    for i, g in enumerate(grupos):
        n = len(g)
        tabela.append({
            "faixa": f"{i / n_faixas:.1f}-{(i + 1) / n_faixas:.1f}",
            "n": n,
            "confianca": sum(c for c, _ in g) / n if n else 0.0,
            "acuracia": sum(a for _, a in g) / n if n else 0.0,
        })
    return tabela


def brier(probs, rotulos):
    """Erro quadrático médio entre a distribuição prevista e o rótulo one-hot."""
    total = 0.0
    for p, r in zip(probs, rotulos):
        total += sum((v - (1.0 if k == r else 0.0)) ** 2 for k, v in p.items())
    return total / len(rotulos)


def nll(probs, rotulos):
    """Log-loss médio (negative log-likelihood)."""
    return -sum(math.log(max(p.get(r, 0.0), EPS)) for p, r in zip(probs, rotulos)) / len(rotulos)


def aplicar_temperatura(p, t):
    """Suaviza (t > 1) ou afia (t < 1) uma distribuição.

    Equivale a dividir os logits por t: softmax(log(p) / t).
    """
    logits = {k: math.log(max(v, EPS)) / t for k, v in p.items()}
    maior = max(logits.values())
    expo = {k: math.exp(v - maior) for k, v in logits.items()}
    soma = sum(expo.values())
    return {k: v / soma for k, v in expo.items()}


def ajustar_temperatura(probs, rotulos, t_min=0.05, t_max=10.0, iteracoes=80):
    """Encontra a temperatura que minimiza o log-loss no holdout.

    Busca pela razão áurea (golden-section): simples, sem numpy, e o log-loss
    em função de t é unimodal na prática.
    """
    def custo(t):
        return nll([aplicar_temperatura(p, t) for p in probs], rotulos)

    razao = (math.sqrt(5) - 1) / 2
    a, b = math.log(t_min), math.log(t_max)
    c, d = b - razao * (b - a), a + razao * (b - a)
    fc, fd = custo(math.exp(c)), custo(math.exp(d))
    for _ in range(iteracoes):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - razao * (b - a)
            fc = custo(math.exp(c))
        else:
            a, c, fc = c, d, fd
            d = a + razao * (b - a)
            fd = custo(math.exp(d))
    return math.exp((a + b) / 2)


def relatorio(probs, rotulos, n_faixas=10):
    """Resumo pronto para imprimir ou salvar."""
    return {
        "n": len(rotulos),
        "acuracia": round(acuracia(probs, rotulos), 4),
        "ece": round(ece(probs, rotulos, n_faixas), 4),
        "brier": round(brier(probs, rotulos), 4),
        "nll": round(nll(probs, rotulos), 4),
    }
