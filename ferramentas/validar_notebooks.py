"""Valida os notebooks sem GPU.

1. Todo .ipynb é JSON válido no formato nbformat 4.
2. Toda célula de código compila (comandos ! e % viram 'pass' antes do ast.parse).
3. O notebook 00 (só stdlib) é EXECUTADO de verdade, trocando /content pelo repositório.

Uso:  python ferramentas/validar_notebooks.py
"""

import ast
import json
import os
import re
import sys
import tempfile

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PASTA = os.path.join(RAIZ, "notebooks")


def limpar_magicas(fonte):
    linhas = []
    for linha in fonte.split("\n"):
        recuo = re.match(r"\s*", linha).group(0)
        resto = linha[len(recuo):]
        if resto.startswith(("!", "%")):
            linhas.append(recuo + "pass")
        elif linhas and linhas[-1].rstrip().endswith("pass") and linha.startswith((" ", "\t")) and resto.startswith('"'):
            continue  # continuação de comando shell com barra invertida
        else:
            linhas.append(linha)
    return "\n".join(linhas)


def celulas_codigo(nb):
    return ["".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code"]


def validar_sintaxe(caminho):
    with open(caminho, encoding="utf-8") as f:
        nb = json.load(f)
    assert nb["nbformat"] == 4, "nbformat diferente de 4"
    erros = []
    for i, fonte in enumerate(celulas_codigo(nb), 1):
        try:
            ast.parse(limpar_magicas(fonte))
        except SyntaxError as e:
            erros.append(f"célula de código {i}: {e}")
    return nb, erros


def executar_nb00(nb):
    saidas = tempfile.mkdtemp()
    escopo = {}
    for fonte in celulas_codigo(nb):
        fonte = fonte.replace("/content/OSINTIA", RAIZ).replace("/content/saidas", saidas)
        exec(compile(limpar_magicas(fonte), "nb00", "exec"), escopo)
    return escopo


def main():
    falhas = 0
    nomes = sorted(n for n in os.listdir(PASTA) if n.endswith(".ipynb"))
    for nome in nomes:
        nb, erros = validar_sintaxe(os.path.join(PASTA, nome))
        status = "OK" if not erros else "FALHA"
        print(f"[{status}] {nome}: {len(nb['cells'])} células, sintaxe {'válida' if not erros else 'inválida'}")
        for e in erros:
            print("   ", e)
        falhas += bool(erros)
        if nome.startswith("00_") and not erros:
            sys.path.insert(0, RAIZ)
            escopo = executar_nb00(nb)
            print(f"[OK] {nome}: executado de ponta a ponta (teto do professor = {escopo['teto']:.3f}, T = {escopo['T']:.2f})")
    print(f"\n{len(nomes)} notebooks, {falhas} com falha")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
