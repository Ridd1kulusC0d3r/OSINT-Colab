#!/usr/bin/env bash
# OSINTIA - lançador para Linux: roda os testes e a auditoria do caso de demonstração.
cd "$(dirname "$0")" || exit 1
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then echo "Python 3 não encontrado. Instale em https://www.python.org/downloads/"; read -r -p "Enter para sair"; exit 1; fi
echo "== Testes do núcleo =="; "$PY" -m unittest discover -s testes
echo; echo "== Auditoria do caso de demonstração =="; "$PY" -m osintia auditar dados/demo/triagem_perfis.jsonl
echo; read -r -p "Pronto. Pressione Enter para fechar."
