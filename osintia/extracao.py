"""Extração determinística de identificadores brasileiros — só stdlib.

Modelos como o GLiNER acham entidades por contexto, mas erram dígitos.
Regras com dígito verificador acertam o formato, mas não entendem contexto.
O notebook 02 combina os dois: o modelo propõe, a regra confirma.
"""

import ipaddress
import re

RE_CPF = re.compile(r"(?<!\d)(\d{3}\.?\d{3}\.?\d{3}-?\d{2})(?!\d)")
RE_CNPJ = re.compile(r"(?<!\d)(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})(?!\d)")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
RE_TELEFONE = re.compile(r"(?:\+?55\s?)?\(?(\d{2})\)?\s?(9?\d{4})[-\s]?(\d{4})(?!\d)")
RE_IPV4 = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])")
RE_HANDLE = re.compile(r"(?<![\w@])@([A-Za-z0-9_.]{3,30})")
RE_URL = re.compile(r"https?://[^\s<>\"')]+")

DDDS_VALIDOS = {
    11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 51, 53, 54, 55, 61, 62, 63, 64, 65, 66, 67, 68,
    69, 71, 73, 74, 75, 77, 79, 81, 82, 83, 84, 85, 86, 87, 88, 89, 91, 92, 93, 94, 95,
    96, 97, 98, 99,
}


def so_digitos(texto):
    return re.sub(r"\D", "", texto)


def cpf_valido(cpf):
    d = so_digitos(cpf)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d[i]) * (tamanho + 1 - i) for i in range(tamanho))
        dv = (soma * 10) % 11 % 10
        if dv != int(d[tamanho]):
            return False
    return True


def cnpj_valido(cnpj):
    d = so_digitos(cnpj)
    if len(d) != 14 or d == d[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, pos in ((pesos1, 12), (pesos2, 13)):
        resto = sum(int(d[i]) * pesos[i] for i in range(pos)) % 11
        dv = 0 if resto < 2 else 11 - resto
        if dv != int(d[pos]):
            return False
    return True


def telefone_valido(ddd, numero):
    return int(ddd) in DDDS_VALIDOS and len(numero) in (8, 9) and (len(numero) == 8 or numero[0] == "9")


def ip_publico(ip):
    try:
        return ipaddress.ip_address(ip).is_global
    except ValueError:
        return False


def extrair(texto):
    """Devolve lista de entidades {tipo, valor, inicio, fim, valido}."""
    achados = []

    def add(tipo, m, valido, valor=None):
        achados.append({"tipo": tipo, "valor": valor or m.group(0), "inicio": m.start(), "fim": m.end(), "valido": valido})

    for m in RE_CNPJ.finditer(texto):
        add("cnpj", m, cnpj_valido(m.group(1)))
    for m in RE_CPF.finditer(texto):
        if not any(a["inicio"] <= m.start() < a["fim"] for a in achados):
            add("cpf", m, cpf_valido(m.group(1)))
    for m in RE_EMAIL.finditer(texto):
        add("email", m, True)
    for m in RE_URL.finditer(texto):
        add("url", m, True)
    for m in RE_IPV4.finditer(texto):
        try:
            ipaddress.ip_address(m.group(1))
            add("ip", m, True)
        except ValueError:
            pass
    ocupados = [(a["inicio"], a["fim"]) for a in achados]
    for m in RE_TELEFONE.finditer(texto):
        if any(i <= m.start() < f for i, f in ocupados):
            continue
        add("telefone", m, telefone_valido(m.group(1), m.group(2) + m.group(3)))
    for m in RE_HANDLE.finditer(texto):
        if not any(a["tipo"] == "email" and a["inicio"] <= m.start() < a["fim"] for a in achados):
            add("handle", m, True)
    return sorted(achados, key=lambda a: a["inicio"])


def mascarar(texto, tipos=("cpf", "cnpj", "telefone", "email")):
    """Substitui identificadores sensíveis por [TIPO] — útil para LGPD em relatórios."""
    partes, cursor = [], 0
    for a in extrair(texto):
        if a["tipo"] in tipos and a["inicio"] >= cursor:
            partes.append(texto[cursor:a["inicio"]])
            partes.append(f"[{a['tipo'].upper()}]")
            cursor = a["fim"]
    partes.append(texto[cursor:])
    return "".join(partes)
