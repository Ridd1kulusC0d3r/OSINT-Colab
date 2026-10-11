# Relatório de testes

**Data:** 10/10/2026 · **Ambiente:** contêiner Linux em nuvem, Python 3.13, sem GPU, sem acesso ao Hugging Face · **Versão:** 1.0.0

## Resumo

| Verificação | Comando | Resultado |
|---|---|---|
| Testes unitários do núcleo | `python -m unittest discover -s testes -v` | **24/24 aprovados** |
| Compatibilidade de sintaxe com Python 3.9 | `ast.parse(..., feature_version=(3, 9))` em todos os `.py` | Aprovado |
| Notebooks 00–06: JSON nbformat 4 e sintaxe de todas as células | `python ferramentas/validar_notebooks.py` | **7/7 aprovados** |
| Notebook 00 executado de ponta a ponta | idem (troca `/content` pelo repositório) | Aprovado |
| CLI `auditar`, `esquemas`, `mascarar` | `python -m osintia ...` | Aprovado |
| Lançador Linux | `./rodar-no-linux.sh` | Aprovado |
| Manual HTML: tags balanceadas | `html.parser` | Aprovado |
| Notebooks 01–06 executados em GPU | — | **Não executados** (ver limites) |

## Cobertura dos testes unitários

| Módulo | O que é testado |
|---|---|
| `calibracao` | ECE detecta modelo superconfiante (>0,2); temperatura >1 reduz ECE para <0,05 sem mudar a acurácia; soma das probabilidades preservada; Brier perfeito = 0 |
| `auditoria` | Concordância e kappa; erro em listas de tamanhos diferentes; aluno que copia o gold dispara o alerta de decoração, mostra lacuna >0,1 e lista erros herdados no caso de demonstração; matriz de confusão |
| `roteamento` | Limiar global; limiar por opção; varredura de cobertura; código do Almirantado e rejeição de código inválido |
| `esquemas` | Os cinco esquemas do catálogo passam na validação; aviso acima de 20 opções descritas; erro acima de 10 níveis; opções de `noul` |
| `dados` | Gold suave a partir de 3 amostras; formato do caso de demonstração; holdout reprodutível |
| `custodia` | Cadeia íntegra; detecção de arquivo modificado; detecção de linha editada no manifesto |
| `extracao` | CPF e CNPJ válidos e inválidos (dígito verificador e sequência repetida); extração de handle, telefone, e-mail, CPF e IP; mascaramento; IP público × privado |

## Saída do notebook 00 (trechos)

```
teto do professor:  0.915
gold x humano:      0.833
kappa gold x humano: 0.744

vs gold:   {'n': 400, 'acuracia': 1.0, 'ece': 0.0617, 'brier': 0.0422, 'nll': 0.0764}
vs humano: {'n': 400, 'acuracia': 0.8325, 'ece': 0.1925, 'brier': 0.3472, 'nll': 4.1624}
67 erros que a métrica oficial chamaria de acerto.

antes:  {'n': 400, 'acuracia': 0.7175, 'ece': 0.121, ...}
T = 1.60
depois: {'n': 400, 'acuracia': 0.7175, 'ece': 0.0481, ...}

{'limiar': 0.6, 'cobertura': 0.8225, 'acuracia_automatica': 0.7234}
{'limiar': 0.7, 'cobertura': 0.41, 'acuracia_automatica': 0.7805}

problemas: nenhum, cadeia íntegra
```

## Limites desta rodada

- **GPU e downloads de modelos.** O ambiente de construção não tinha GPU nem acesso ao Hugging Face (conexão recusada pela política de rede). Os notebooks 01 a 06 foram validados por estrutura e sintaxe, não por execução.
- **Base do notebook 01.** Escrito sobre o código oficial `Qwen3_5_(4B)-Decision` da Unsloth, lido em 10/10/2026: mesmas classes (`FastDecisionModel`, `DecisionTrainer`), mesma instalação e mesmos parâmetros de LoRA. A diferença é o dataset (OSINT, gold no mesmo formato do `typed-decisions`) e as células de auditoria.
- **Pontos a observar na primeira execução real:**
  1. Se `FastDecisionModel.build_dataset` aceita o gold da demonstração sem descartar decisões (a célula imprime quantas foram descartadas).
  2. Tempo de treino no T4 com 3 épocas sobre ~320 linhas.
  3. No notebook 06, o viés de comprimento de opções com muitos tokens.
- **Dados sintéticos.** O caso de demonstração prova o mecanismo da auditoria; não mede desempenho em dados reais.

## Como reproduzir

```bash
python -m unittest discover -s testes -v
python ferramentas/gerar_notebooks.py && git diff --exit-code notebooks/
python ferramentas/validar_notebooks.py
```

O workflow `.github/workflows/testes.yml` roda as três etapas em Python 3.9 e 3.12 a cada *push*.
