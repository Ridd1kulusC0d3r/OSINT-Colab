# Relatório de testes

**Data:** 11/10/2026 · **Ambiente:** contêiner Linux em nuvem, Python 3.13, sem GPU, sem acesso ao Hugging Face, crt.sh ou Wayback · **Versão:** 1.1.0

## Resumo

| Verificação | Comando | Resultado |
|---|---|---|
| Testes unitários do núcleo | `python -m unittest discover -s testes -v` | **43/43 aprovados** (sem avisos de recurso) |
| Compatibilidade de sintaxe com Python 3.9 | `ast.parse(..., feature_version=(3, 9))` em todos os `.py` | Aprovado |
| Notebooks 00–09: JSON nbformat 4 e sintaxe de todas as células | `python ferramentas/validar_notebooks.py` | **10/10 aprovados** |
| Notebook 00 executado de ponta a ponta | idem (troca `/content` pelo repositório) | Aprovado |
| Notebook 09 executado de ponta a ponta | idem | Aprovado (4 grupos; cobertura 1,0; precisão 0,86) |
| Notebook 08, Parte A (auditoria sem GPU) | execução das células até o import do GeoCLIP | Aprovado (ECE 0,21 a 25 km) |
| Notebook 07, células offline (variantes) | idem | Aprovado (103 variantes de `bancoaurora`) |
| CLI `auditar`, `esquemas`, `mascarar`, `variantes`, `coordenacao` | `python -m osintia ...` | Aprovado |
| Lançador Linux | `./rodar-no-linux.sh` | Aprovado |
| Manual HTML: tags balanceadas | `html.parser` | Aprovado |
| Manual HTML sem rolagem horizontal (1100 px e 390 px) | Playwright + Chromium | Aprovado |
| Notebooks 01–06 e 08 (Parte B) executados em GPU | — | **Não executados** (ver limites) |
| Notebook 07 contra serviços reais | — | **Não executado**: a rede do ambiente bloqueia crt.sh e Wayback; os *parsers* foram testados com respostas simuladas |

## Cobertura dos testes unitários

| Módulo | O que é testado |
|---|---|
| `calibracao` | ECE detecta modelo superconfiante (>0,2); temperatura >1 reduz ECE para <0,05 sem mudar a acurácia; soma das probabilidades preservada; Brier perfeito = 0 |
| `auditoria` | Concordância e kappa; erro em listas de tamanhos diferentes; aluno que copia o gold dispara o alerta de decoração, mostra lacuna >0,1 e lista erros herdados no caso de demonstração; matriz de confusão |
| `roteamento` | Limiar global; limiar por opção; varredura de cobertura; código do Almirantado e rejeição de código inválido |
| `esquemas` | Os cinco esquemas do catálogo passam na validação; aviso acima de 20 opções descritas; erro acima de 10 níveis; opções de `noul` |
| `dados` | Gold suave a partir de 3 amostras; formato do caso de demonstração; holdout reprodutível |
| `custodia` | Cadeia íntegra; detecção de arquivo modificado; detecção de linha editada no manifesto |
| `coleta` | Parse do crt.sh com deduplicação e curinga `*.`; montagem das URLs crt.sh, CDX e `id_`; parse do CDX (inclusive vazio); IDs UA, G-, GTM, pixel do Facebook e AdSense; IDs compartilhados ignorando erros; variantes (homóglifo, sufixo, separador, letra dobrada e omitida) |
| `coordenacao` | Jaccard de trigramas; domínio sem `www`; detecção das 3 células (cobertura 1,0, precisão ≥ 0,8); a armadilha da imprensa aparece como grupo; nenhum grupo traz atribuição; contas orgânicas isoladas não formam grupo; timestamp ISO; GraphML |
| `geo` | Haversine BH–SP ≈ 489 km; conversão do GPS do EXIF; acurácia monotônica por distância; ECE alto no geolocalizador superconfiante; dispersão do top-k; KML |
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

## Saída do notebook 09

```
Grupo 1: 7 contas, densidade 1.0, sinais {'co_link': 42, 'co_dominio': 42, 'co_repost': 39, 'co_texto': 96}
Grupo 2: 6 contas, densidade 1.0, sinais {'co_link': 44, 'co_dominio': 44, 'co_repost': 13, 'co_texto': 59}
Grupo 3: 5 contas, densidade 1.0, sinais {'co_link': 13, 'co_dominio': 13, 'co_repost': 17, 'co_texto': 36}
Grupo 4: 3 contas, densidade 1.0, sinais {'co_link': 3, 'co_dominio': 3, 'co_texto': 9}   <- imprensa
{'precisao': 0.8571, 'cobertura': 1.0, 'marcadas': 21, 'coordenadas_reais': 18}
```

## Saída do notebook 08, Parte A

```
acurácia por distância: {'rua': 0.0083, 'cidade': 0.4417, 'regiao': 0.4417, 'pais': 0.5625, 'continente': 0.8833, 'mediana_km': 357.5}
ECE no raio de cidade (25 km): 0.2098
marco_urbano   acerto em 25 km: 86%    interior   acerto em 25 km: 10%
top-5 estável : 123 fotos, acerto em 25 km = 68%
top-5 disperso: 117 fotos, acerto em 25 km = 19%
```

## Limites desta rodada

- **GPU e downloads de modelos.** O ambiente de construção não tinha GPU nem acesso ao Hugging Face (conexão recusada pela política de rede). Os notebooks 01 a 06 foram validados por estrutura e sintaxe, não por execução.
- **Base do notebook 01.** Escrito sobre o código oficial `Qwen3_5_(4B)-Decision` da Unsloth, lido em 10/10/2026: mesmas classes (`FastDecisionModel`, `DecisionTrainer`), mesma instalação e mesmos parâmetros de LoRA. A diferença é o dataset (OSINT, gold no mesmo formato do `typed-decisions`) e as células de auditoria.
- **Pontos a observar na primeira execução real:**
  1. Se `FastDecisionModel.build_dataset` aceita o gold da demonstração sem descartar decisões (a célula imprime quantas foram descartadas).
  2. Tempo de treino no T4 com 3 épocas sobre ~320 linhas.
  3. No notebook 06, o viés de comprimento de opções com muitos tokens.
- **Notebook 07.** Os comandos do Maigret (`--json ndjson --folderoutput`) e do Holehe (`--only-used --csv`) seguem a documentação e os notebooks da Bellingcat, mas não foram executados aqui. Na primeira execução, confira se aparecem arquivos em `/content/saidas/maigret/`.
- **Notebook 08.** A chamada `GeoCLIP().predict(caminho, top_k=5)` segue o README oficial. O teste real depende de fotos com GPS do próprio usuário.
- **Dados sintéticos.** O caso de demonstração prova o mecanismo da auditoria; não mede desempenho em dados reais.

## Como reproduzir

```bash
python -m unittest discover -s testes -v
python ferramentas/gerar_demo.py && python ferramentas/gerar_demo_coordenacao.py && git diff --exit-code dados/
python ferramentas/gerar_notebooks.py && git diff --exit-code notebooks/
python ferramentas/validar_notebooks.py
```

O workflow `.github/workflows/testes.yml` roda as três etapas em Python 3.9 e 3.12 a cada *push*.
