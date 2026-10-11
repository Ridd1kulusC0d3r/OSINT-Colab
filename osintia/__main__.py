"""Linha de comando do OSINTIA (só stdlib).

    python -m osintia auditar dados/demo/triagem_perfis.jsonl --pergunta perfil
    python -m osintia extrair "texto com CPF 529.982.247-25"
    python -m osintia mascarar "texto com CPF 529.982.247-25"
    python -m osintia verificar saidas/manifesto.jsonl
    python -m osintia esquemas
"""

import argparse
import json
import sys

from . import auditoria, calibracao, custodia, dados, esquemas, extracao


def cmd_auditar(a):
    linhas = dados.carregar_jsonl(a.arquivo)
    gold = dados.rotulos(linhas, a.pergunta)
    print(f"Arquivo: {a.arquivo} | {len(linhas)} linhas | pergunta: {a.pergunta}\n")
    if "amostra_professor_extra" in linhas[0]:
        extra = [l["amostra_professor_extra"][a.pergunta] for l in linhas]
        print(f"Teto do professor (amostra extra x gold): {auditoria.teto_do_professor([extra], gold):.3f}")
    if "rotulo_humano" in linhas[0]:
        humano = [l["rotulo_humano"][a.pergunta] for l in linhas]
        probs = [json.loads(l["gold"])[a.pergunta]["probabilities"] for l in linhas]
        print(f"Gold x humano: {auditoria.concordancia(gold, humano):.3f} (kappa {auditoria.kappa_cohen(gold, humano):.3f})")
        print("Calibração do gold contra o humano:", calibracao.relatorio(probs, humano))
        print("\nMatriz (linhas = humano, colunas = gold):")
        print(auditoria.imprimir_matriz(humano, gold))
        print(f"\nItens em que o gold discorda do humano: {sum(g != h for g, h in zip(gold, humano))}")


def cmd_extrair(a):
    for e in extracao.extrair(a.texto):
        print(json.dumps(e, ensure_ascii=False))


def cmd_mascarar(a):
    print(extracao.mascarar(a.texto))


def cmd_verificar(a):
    problemas = custodia.verificar(a.manifesto)
    print("\n".join(problemas) if problemas else "Cadeia íntegra.")
    return 1 if problemas else 0


def cmd_esquemas(_):
    for nome, esquema in esquemas.CATALOGO.items():
        tipos = ", ".join(f"{k} ({v['type']})" for k, v in esquema.items())
        print(f"{nome}: {tipos}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="osintia", description="Núcleo OSINTIA: auditoria, extração e custódia")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("auditar", help="teto do professor e lacuna humana de um JSONL de decisões")
    s.add_argument("arquivo")
    s.add_argument("--pergunta", default="perfil")
    s.set_defaults(func=cmd_auditar)

    s = sub.add_parser("extrair", help="extrai CPF, CNPJ, telefone, e-mail, IP, URL e handles")
    s.add_argument("texto")
    s.set_defaults(func=cmd_extrair)

    s = sub.add_parser("mascarar", help="mascara identificadores pessoais (LGPD)")
    s.add_argument("texto")
    s.set_defaults(func=cmd_mascarar)

    s = sub.add_parser("verificar", help="verifica a cadeia de custódia de um manifesto")
    s.add_argument("manifesto")
    s.set_defaults(func=cmd_verificar)

    s = sub.add_parser("esquemas", help="lista as perguntas OSINT prontas")
    s.set_defaults(func=cmd_esquemas)

    a = p.parse_args(argv)
    return a.func(a) or 0


if __name__ == "__main__":
    sys.exit(main())
