"""OSINTIA — núcleo stdlib para modelos de IA aplicados a OSINT.

Este pacote não depende de nada além da biblioteca padrão do Python.
Ele cuida da parte que os notebooks de GPU não resolvem sozinhos:

- calibracao: ECE, Brier, tabela de confiabilidade e temperature scaling
- auditoria:  concordância, kappa de Cohen e o "teto do professor"
- roteamento: decisão com limiar e encaminhamento para revisão humana
- esquemas:   perguntas OSINT prontas no formato choice / noul / score
- dados:      leitura e escrita de JSONL, gold suave, divisão de holdout
- custodia:   manifesto SHA-256 encadeado (cadeia de custódia)
- extracao:   validadores determinísticos BR (CPF, CNPJ, telefone, e-mail, IP)
"""

__version__ = "1.0.0"

from . import auditoria, calibracao, custodia, dados, esquemas, extracao, roteamento

__all__ = [
    "auditoria",
    "calibracao",
    "custodia",
    "dados",
    "esquemas",
    "extracao",
    "roteamento",
]
