"""Auditoria de rótulos — de onde veio a certeza do modelo?

O problema que este módulo resolve:
    Muitos datasets de decisão têm gabarito gerado por outro modelo (o
    "professor"). Um aluno treinado nesse gabarito pode atingir alta acurácia
    e calibração quase perfeita e, mesmo assim, repetir os erros do professor.

Três medidas simples:
    1. teto_do_professor: quanto o professor concorda com o próprio gabarito
       quando você sorteia uma nova resposta dele. É o máximo "honesto".
    2. alerta_de_decoracao: se o aluno passa desse teto, ele está imitando os
       vícios do professor, não aprendendo a tarefa.
    3. lacuna_humana: diferença entre concordar com o gabarito e concordar com
       uma amostra checada por um humano.
"""

from collections import Counter


def concordancia(a, b):
    """Fração de posições em que as duas listas têm o mesmo rótulo."""
    if len(a) != len(b):
        raise ValueError("as listas precisam ter o mesmo tamanho")
    return sum(x == y for x, y in zip(a, b)) / len(a)


def kappa_cohen(a, b):
    """Concordância descontando o acaso (1 = total, 0 = acaso, < 0 = pior)."""
    n = len(a)
    observada = concordancia(a, b)
    ca, cb = Counter(a), Counter(b)
    esperada = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if esperada == 1:
        return 1.0
    return (observada - esperada) / (1 - esperada)


def matriz_confusao(verdade, previsto):
    """Dicionário {(verdade, previsto): contagem}."""
    return dict(Counter(zip(verdade, previsto)))


def imprimir_matriz(verdade, previsto):
    """Texto simples da matriz de confusão, linhas = verdade."""
    classes = sorted(set(verdade) | set(previsto))
    m = matriz_confusao(verdade, previsto)
    largura = max(len(c) for c in classes) + 2
    linhas = [" " * largura + "".join(c.rjust(largura) for c in classes)]
    for v in classes:
        linhas.append(v.ljust(largura) + "".join(str(m.get((v, p), 0)).rjust(largura) for p in classes))
    return "\n".join(linhas)


def teto_do_professor(amostras, gabarito):
    """Concordância média de cada amostra do professor com o gabarito.

    amostras: lista de listas — amostras[i] é a lista de rótulos da i-ésima
              rodada independente do professor sobre os mesmos itens.
    gabarito: lista de rótulos usada como "verdade" no treino.
    """
    valores = [concordancia(s, gabarito) for s in amostras]
    return sum(valores) / len(valores)


def alerta_de_decoracao(acuracia_aluno, teto, margem=0.02):
    """True quando o aluno concorda com o gabarito mais do que o próprio professor."""
    return acuracia_aluno > teto + margem


def lacuna_humana(previsto, gabarito, humano):
    """Compara o modelo com o gabarito e com a verificação humana nos mesmos itens."""
    vs_gabarito = concordancia(previsto, gabarito)
    vs_humano = concordancia(previsto, humano)
    return {
        "modelo_x_gabarito": round(vs_gabarito, 4),
        "modelo_x_humano": round(vs_humano, 4),
        "gabarito_x_humano": round(concordancia(gabarito, humano), 4),
        "lacuna": round(vs_gabarito - vs_humano, 4),
    }


def erros_herdados(previsto, gabarito, humano):
    """Índices onde modelo e gabarito concordam entre si, mas o humano discorda.

    São exatamente os erros que a métrica oficial chama de acerto.
    """
    return [i for i, (p, g, h) in enumerate(zip(previsto, gabarito, humano)) if p == g != h]
