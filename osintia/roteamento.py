"""Roteamento de decisões com humano no circuito.

Regra simples e auditável: se a probabilidade da melhor opção não passa do
limiar, quem decide é o analista. O limiar pode variar por opção, porque o
custo de errar "escalar" não é o mesmo de errar "arquivar".
"""

REVISAO = "REVISAO_HUMANA"


def rotear(probs, limiar=0.70, limiares=None, revisao=REVISAO):
    """Devolve a opção vencedora ou o rótulo de revisão humana.

    probs:    {opcao: probabilidade}
    limiar:   limiar padrão
    limiares: limiares específicos por opção, ex.: {"descartar": 0.9}
    """
    opcao = max(probs, key=probs.get)
    exigido = (limiares or {}).get(opcao, limiar)
    return opcao if probs[opcao] >= exigido else revisao


def rotear_lote(lista_probs, **kwargs):
    return [rotear(p, **kwargs) for p in lista_probs]


def cobertura_e_acuracia(lista_probs, rotulos, limiar=0.70, **kwargs):
    """Quanto o modelo decide sozinho e com que acurácia nesse pedaço.

    Ajuda a escolher o limiar: subir o limiar reduz a cobertura e, num modelo
    calibrado, aumenta a acurácia das decisões automáticas.
    """
    decisoes = rotear_lote(lista_probs, limiar=limiar, **kwargs)
    automaticas = [(d, r) for d, r in zip(decisoes, rotulos) if d != REVISAO]
    cobertura = len(automaticas) / len(rotulos)
    acc = sum(d == r for d, r in automaticas) / len(automaticas) if automaticas else 0.0
    return {"limiar": limiar, "cobertura": round(cobertura, 4), "acuracia_automatica": round(acc, 4)}


def varrer_limiares(lista_probs, rotulos, limiares=(0.5, 0.6, 0.7, 0.8, 0.9, 0.95)):
    return [cobertura_e_acuracia(lista_probs, rotulos, limiar=l) for l in limiares]


# Escala do Almirantado (NATO Admiralty Code), usada em avaliação de fontes.
CONFIABILIDADE_FONTE = {
    "A": "Totalmente confiável",
    "B": "Geralmente confiável",
    "C": "Razoavelmente confiável",
    "D": "Geralmente não confiável",
    "E": "Não confiável",
    "F": "Confiabilidade não pode ser julgada",
}

CREDIBILIDADE_INFORMACAO = {
    "1": "Confirmada por outras fontes",
    "2": "Provavelmente verdadeira",
    "3": "Possivelmente verdadeira",
    "4": "Duvidosa",
    "5": "Improvável",
    "6": "Veracidade não pode ser julgada",
}


def codigo_almirantado(letra, numero):
    """Monta o código no formato usual, ex.: B2."""
    if letra not in CONFIABILIDADE_FONTE or str(numero) not in CREDIBILIDADE_INFORMACAO:
        raise ValueError("código fora da escala do Almirantado")
    return f"{letra}{numero}"
