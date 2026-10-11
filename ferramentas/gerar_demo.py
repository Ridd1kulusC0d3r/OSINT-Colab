"""Gera o caso de demonstração: triagem de perfis que imitam um alvo fictício.

Tudo aqui é sintético. "Banco Aurora" e todos os usernames são inventados.

O que o gerador simula de propósito:
    - uma verdade de referência (rotulo_humano), como se um analista tivesse
      checado cada perfil;
    - um professor (outro modelo) que rotula com ruído e com UM VÍCIO
      sistemático: todo perfil com selo de verificado vira "legitimo", mesmo
      quando é um imitador que comprou o selo;
    - 3 amostras independentes do professor por perfil; o gold é a média delas
      (igual ao que a análise pública aponta no typed-decisions).

Assim dá para ver, na prática, o aluno aprender o vício do professor.

Uso:  python ferramentas/gerar_demo.py
"""

import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from osintia.dados import montar_linha, salvar_jsonl  # noqa: E402
from osintia.esquemas import TRIAGEM_PERFIL  # noqa: E402

SEMENTE = 3407
N = 400
RUIDO_PROFESSOR = 0.12
SAIDA = os.path.join(os.path.dirname(__file__), "..", "dados", "demo", "triagem_perfis.jsonl")

OFICIAL = "bancoaurora"
VARIANTES = [
    "bancoaurora_oficial", "banco.aurora", "bancoaur0ra", "bancoaurora_sac", "bancoauroraa",
    "banc0aurora", "bancoaurora.atendimento", "suporte_bancoaurora", "bancoaurora_br", "bamcoaurora",
]
LEGITIMOS = ["bancoaurora", "bancoaurora_carreiras", "bancoaurora_invest", "bancoaurora_pj"]
BIOS_LEGIT = [
    "Perfil oficial do Banco Aurora. Nunca pedimos senha por mensagem.",
    "Vagas e cultura do Banco Aurora. Link oficial na bio.",
    "Conteúdo sobre investimentos do Banco Aurora. CNPJ na página oficial.",
]
BIOS_IMIT = [
    "Atendimento 24h Banco Aurora! Resolvemos seu problema pelo WhatsApp.",
    "Central de estorno Banco Aurora. Chame no direct com seu CPF.",
    "SAC Aurora - liberação de crédito na hora, envie seus dados.",
    "Suporte oficial* Banco Aurora. Desbloqueio de conta por link.",
]
BIOS_BOT = [
    "Promoções e cupons todo dia!!! Siga e ative as notificações.",
    "Notícias de economia 24/7. Repost automático.",
    "Ganhe pontos e prêmios. Link na bio. Link na bio. Link na bio.",
]


def sortear_perfil(r):
    verdade = r.choices(["legitimo", "imitador", "bot"], weights=[0.30, 0.45, 0.25])[0]
    if verdade == "legitimo":
        user = r.choice(LEGITIMOS)
        dias = r.randint(900, 4000)
        seguidores = r.randint(20_000, 900_000)
        posts_dia = round(r.uniform(0.3, 3.0), 1)
        bio = r.choice(BIOS_LEGIT)
        verificado = r.random() < 0.85
        link = "https://aurora.example/oficial"
        repete = False
    elif verdade == "imitador":
        user = r.choice(VARIANTES)
        dias = r.randint(1, 120)
        seguidores = r.randint(10, 4_000)
        posts_dia = round(r.uniform(0.5, 8.0), 1)
        bio = r.choice(BIOS_IMIT)
        verificado = r.random() < 0.30  # selo comprado: a armadilha do professor
        link = r.choice(["https://aurora-estorno.example", "https://wa.example/5531999990000", "https://bit.example/aurora"])
        repete = r.random() < 0.3
    else:
        user = f"{r.choice(['promo', 'news', 'cupom', 'bot'])}{r.choice(['aurora', 'banco', 'fin'])}{r.randint(10, 9999)}"
        dias = r.randint(5, 700)
        seguidores = r.randint(0, 15_000)
        posts_dia = round(r.uniform(25, 300), 1)
        bio = r.choice(BIOS_BOT)
        verificado = r.random() < 0.05
        link = "https://cupons.example"
        repete = True
    return verdade, {
        "username": user, "dias": dias, "seguidores": seguidores, "posts_dia": posts_dia,
        "bio": bio, "verificado": verificado, "link": link, "repete": repete,
    }


def texto_do_perfil(p):
    linhas = [
        f"Alvo monitorado: @{OFICIAL}",
        f"Perfil analisado: @{p['username']}",
        f"Selo de verificado: {'sim' if p['verificado'] else 'não'}",
        f"Conta criada há {p['dias']} dias",
        f"Seguidores: {p['seguidores']}",
        f"Média de postagens por dia: {p['posts_dia']}",
        f"Bio: {p['bio']}",
        f"Link na bio: {p['link']}",
        f"Conteúdo repetido entre postagens: {'sim' if p['repete'] else 'não'}",
    ]
    return "\n".join(linhas)


def acao_verdadeira(verdade, p):
    if verdade == "imitador":
        golpe = any(t in p["bio"].lower() for t in ("cpf", "dados", "link", "whatsapp", "estorno"))
        return "escalar" if golpe else "monitorar"
    if verdade == "bot":
        return "monitorar" if "aurora" in p["username"] else "arquivar"
    return "arquivar"


def amostra_professor(r, verdade, p):
    """Uma resposta do professor: vício do selo + ruído."""
    if p["verificado"]:
        perfil = "legitimo"
    elif r.random() < RUIDO_PROFESSOR:
        perfil = r.choice([o for o in ("legitimo", "imitador", "bot") if o != verdade])
    else:
        perfil = verdade
    acao = acao_verdadeira(perfil, p) if perfil != "legitimo" else "arquivar"
    if r.random() < RUIDO_PROFESSOR / 2:
        acao = r.choice(["arquivar", "monitorar", "escalar"])
    return perfil, acao


def main():
    r = random.Random(SEMENTE)
    linhas = []
    for i in range(N):
        verdade, p = sortear_perfil(r)
        amostras = [amostra_professor(r, verdade, p) for _ in range(4)]
        gold_amostras, amostra_extra = amostras[:3], amostras[3]
        linha = montar_linha(
            f"demo_{i:04d}",
            texto_do_perfil(p),
            TRIAGEM_PERFIL,
            {
                "perfil": [a[0] for a in gold_amostras],
                "acao": [a[1] for a in gold_amostras],
            },
        )
        linha["rotulo_humano"] = {"perfil": verdade, "acao": acao_verdadeira(verdade, p)}
        # Uma 4ª amostra do professor, independente do gold: serve para medir o teto.
        linha["amostra_professor_extra"] = {"perfil": amostra_extra[0], "acao": amostra_extra[1]}
        linhas.append(linha)
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    salvar_jsonl(linhas, SAIDA)
    print(f"{len(linhas)} linhas gravadas em {os.path.normpath(SAIDA)}")
    print("exemplo de gold:", json.loads(linhas[0]["gold"]))


if __name__ == "__main__":
    main()
