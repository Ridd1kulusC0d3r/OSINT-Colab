"""Perguntas OSINT prontas no formato de modelo de decisão.

Formato (o mesmo do FastDecisionModel da Unsloth e da API Laya/Jev):

    choice -> {"type": "choice", "instructions": str, "criteria": {opcao: descricao}}
    noul   -> {"type": "noul",   "instructions": str}            # sim/não
    score  -> {"type": "score",  "instructions": str, "criteria": [nivel_baixo, ..., nivel_alto]}

Limites documentados pela Unsloth para a API Laya: até 64 perguntas por
requisição, 255 opções por choice, 10 níveis por score, e as descrições das
opções dividem um orçamento fixo de tokens (passando de ~20 opções descritas,
os textos começam a ser cortados). validar() checa tudo isso.
"""

LIMITE_PERGUNTAS = 64
LIMITE_OPCOES = 255
LIMITE_NIVEIS = 10
AVISO_OPCOES_DESCRITAS = 20

TRIAGEM_PERFIL = {
    "perfil": {
        "type": "choice",
        "instructions": "Este perfil de rede social é legítimo, um imitador do alvo ou automatizado?",
        "criteria": {
            "legitimo": "conta autêntica da pessoa ou organização que diz ser",
            "imitador": "conta que se passa pelo alvo: username parecido, foto copiada, golpe ou phishing",
            "bot": "conta automatizada: postagem em rajadas, conteúdo repetido, sem interação humana",
        },
    },
    "acao": {
        "type": "choice",
        "instructions": "O que a equipe de inteligência deve fazer com este perfil?",
        "criteria": {
            "arquivar": "sem risco, apenas registrar",
            "monitorar": "acompanhar mudanças e novas postagens",
            "escalar": "risco ativo ao alvo: pedir remoção e avisar o cliente",
        },
    },
}

CONFIABILIDADE_FONTE = {
    "fonte": {
        "type": "score",
        "instructions": "Qual a confiabilidade desta fonte na escala do Almirantado?",
        "criteria": [
            "F - não pode ser julgada",
            "E - não confiável",
            "D - geralmente não confiável",
            "C - razoavelmente confiável",
            "B - geralmente confiável",
            "A - totalmente confiável",
        ],
    },
    "corroborada": {
        "type": "noul",
        "instructions": "A informação é confirmada por outra fonte independente citada no texto?",
    },
}

TRIAGEM_IOC = {
    "acao": {
        "type": "choice",
        "instructions": "O que fazer com este indicador de comprometimento?",
        "criteria": {
            "bloquear": "malicioso com evidência clara",
            "monitorar": "suspeito, sem evidência suficiente",
            "descartar": "benigno ou infraestrutura legítima compartilhada",
        },
    },
    "falso_positivo": {
        "type": "noul",
        "instructions": "Há sinais de que é um falso positivo (CDN, serviço legítimo, IP compartilhado)?",
    },
}

AMEACA_POSTAGEM = {
    "classe": {
        "type": "choice",
        "instructions": "Esta postagem representa uma ameaça?",
        "criteria": {
            "ameaca_real": "intenção, alvo e capacidade plausíveis",
            "ruido": "desabafo, exagero ou linguagem agressiva sem intenção concreta",
            "satira": "humor, ironia ou meme",
        },
    },
    "urgencia": {
        "type": "score",
        "instructions": "Qual a urgência de encaminhamento?",
        "criteria": ["sem urgência", "nas próximas 72h", "nas próximas 24h", "imediata"],
    },
}

TRIAGEM_VAZAMENTO = {
    "relevancia": {
        "type": "choice",
        "instructions": "Este trecho de vazamento ou paste é relevante para o cliente monitorado?",
        "criteria": {
            "credencial_cliente": "usuário e senha do domínio do cliente",
            "dado_pessoal": "dados pessoais de funcionários ou clientes",
            "infraestrutura": "IPs, chaves, configurações ou código do cliente",
            "irrelevante": "sem relação com o cliente",
        },
    },
    "recente": {"type": "noul", "instructions": "Há indícios de que o vazamento é recente (últimos 90 dias)?"},
}

CATALOGO = {
    "triagem_perfil": TRIAGEM_PERFIL,
    "confiabilidade_fonte": CONFIABILIDADE_FONTE,
    "triagem_ioc": TRIAGEM_IOC,
    "ameaca_postagem": AMEACA_POSTAGEM,
    "triagem_vazamento": TRIAGEM_VAZAMENTO,
}


def opcoes(pergunta):
    """Lista de saídas possíveis de uma pergunta."""
    tipo = pergunta["type"]
    if tipo == "choice":
        return list(pergunta["criteria"])
    if tipo == "score":
        return list(range(len(pergunta["criteria"])))
    if tipo == "noul":
        return [True, False]
    raise ValueError(f"tipo desconhecido: {tipo}")


def validar(perguntas):
    """Devolve (erros, avisos). Lista de erros vazia = esquema utilizável."""
    erros, avisos = [], []
    if not isinstance(perguntas, dict) or not perguntas:
        return ["o esquema precisa ser um dicionário não vazio"], avisos
    if len(perguntas) > LIMITE_PERGUNTAS:
        erros.append(f"{len(perguntas)} perguntas; o limite é {LIMITE_PERGUNTAS}")
    for nome, p in perguntas.items():
        tipo = p.get("type")
        if tipo not in ("choice", "noul", "score"):
            erros.append(f"{nome}: tipo inválido {tipo!r}")
            continue
        if not p.get("instructions"):
            erros.append(f"{nome}: falta 'instructions'")
        if tipo == "choice":
            crit = p.get("criteria")
            if not isinstance(crit, dict) or len(crit) < 2:
                erros.append(f"{nome}: choice precisa de 'criteria' com 2+ opções")
            elif len(crit) > LIMITE_OPCOES:
                erros.append(f"{nome}: {len(crit)} opções; o limite é {LIMITE_OPCOES}")
            elif len(crit) > AVISO_OPCOES_DESCRITAS:
                avisos.append(f"{nome}: {len(crit)} opções descritas; acima de ~20 as descrições são cortadas e a acurácia tende a cair")
        if tipo == "score":
            crit = p.get("criteria")
            if not isinstance(crit, list) or len(crit) < 2:
                erros.append(f"{nome}: score precisa de 'criteria' em lista com 2+ níveis")
            elif len(crit) > LIMITE_NIVEIS:
                erros.append(f"{nome}: {len(crit)} níveis; o limite é {LIMITE_NIVEIS}")
    return erros, avisos
