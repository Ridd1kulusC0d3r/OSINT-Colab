"""Linha de comando do OSINTIA (só stdlib).

    python -m osintia auditar dados/demo/triagem_perfis.jsonl --pergunta perfil
    python -m osintia extrair "texto com CPF 529.982.247-25"
    python -m osintia mascarar "texto com CPF 529.982.247-25"
    python -m osintia verificar saidas/manifesto.jsonl
    python -m osintia esquemas
    python -m osintia variantes bancoaurora
    python -m osintia coordenacao dados/demo/campanha_coordenada.csv --minimo 3
    python -m osintia analytics pagina.html
"""

import argparse
import json
import sys

from . import auditoria, calibracao, coleta, coordenacao, custodia, dados, esquemas, extracao


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


def cmd_variantes(a):
    for v in coleta.variantes(a.nome, max_itens=a.max):
        print(v)


def cmd_coordenacao(a):
    msgs = coordenacao.ler_csv(a.csv)
    arestas = coordenacao.grafo(coordenacao.sinais(msgs, janela=a.janela), minimo=a.minimo)
    grupos = coordenacao.grupos(arestas)
    print(f"{len(msgs)} mensagens | {len(arestas)} arestas | {len(grupos)} grupos\n")
    for i, g in enumerate(grupos, 1):
        r = coordenacao.resumo_grupo(g, arestas, msgs)
        print(f"Grupo {i}: {r['tamanho']} contas, densidade {r['densidade']}, sinais {r['sinais']}")
        print("   ", ", ".join(r["contas"][:8]) + (" ..." if r["tamanho"] > 8 else ""))
    print("\n" + coordenacao.AVISO)


def cmd_analytics(a):
    with open(a.html, encoding="utf-8", errors="replace") as f:
        print(json.dumps(coleta.ids_analytics(f.read()), indent=2))


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

    s = sub.add_parser("variantes", help="variantes de imitação de um username ou marca")
    s.add_argument("nome")
    s.add_argument("--max", type=int, default=60)
    s.set_defaults(func=cmd_variantes)

    s = sub.add_parser("coordenacao", help="grupos de contas coordenadas a partir de um CSV")
    s.add_argument("csv")
    s.add_argument("--janela", type=int, default=60)
    s.add_argument("--minimo", type=float, default=3.0)
    s.set_defaults(func=cmd_coordenacao)

    s = sub.add_parser("analytics", help="IDs de analytics (UA-, G-, GTM-, pixel) em um arquivo HTML")
    s.add_argument("html")
    s.set_defaults(func=cmd_analytics)

    a = p.parse_args(argv)
    return a.func(a) or 0


if __name__ == "__main__":
    sys.exit(main())
