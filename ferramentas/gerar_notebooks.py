"""Gera os notebooks Colab do OSINTIA a partir de especificações em Python.

Por que gerar em vez de editar o .ipynb na mão?
    - diffs legíveis no GitHub (o código está aqui, não num JSON gigante)
    - todos os notebooks seguem o mesmo cabeçalho, setup e rodapé
    - ferramentas/validar_notebooks.py checa a sintaxe de cada célula

Uso:  python ferramentas/gerar_notebooks.py
"""

import json
import os

REPO = "Ridd1kulusC0d3r/OSINTIA"
PASTA = os.path.join(os.path.dirname(__file__), "..", "notebooks")


def colab(nome):
    return f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{nome}"


def cabecalho(nome, titulo, resumo, gpu, tempo):
    hw = "GPU T4 gratuita (Ambiente de execução → Alterar tipo → T4 GPU)" if gpu else "CPU (não precisa de GPU)"
    return f"""<a href="{colab(nome)}" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Abrir no Colab"/></a>

# {titulo}

**OSINTIA** · modelos de IA para OSINT, reconstruídos e auditáveis · [repositório](https://github.com/{REPO})

{resumo}

| | |
|---|---|
| **Hardware** | {hw} |
| **Tempo estimado** | {tempo} |
| **Como rodar** | Menu *Ambiente de execução* → *Executar tudo* |

> ⚖️ Uso ético: só fontes abertas, finalidade legítima e respeito à LGPD. Os dados de demonstração são **fictícios**. Leia `docs/METODOLOGIA.md`."""


SETUP_REPO = """# Baixa o OSINTIA (núcleo em Python puro: calibração, auditoria, roteamento, custódia)
!git clone -q https://github.com/Ridd1kulusC0d3r/OSINTIA.git /content/OSINTIA 2>/dev/null || git -C /content/OSINTIA pull -q
import sys
sys.path.insert(0, "/content/OSINTIA")
from osintia import auditoria, calibracao, custodia, dados, esquemas, extracao, roteamento
print("OSINTIA pronto")"""

INSTALA_UNSLOTH = """%%capture
# Instalação igual à dos notebooks oficiais da Unsloth (LGPL-3.0), mantida para compatibilidade.
import os, importlib.util
!pip install --upgrade -qqq uv
if importlib.util.find_spec("torch") is None or "COLAB_" in "".join(os.environ.keys()):
    try: import numpy, PIL; _numpy = f"numpy=={numpy.__version__}"; _pil = f"pillow=={PIL.__version__}"
    except: _numpy = "numpy"; _pil = "pillow"
    !uv pip install -qqq \\
        "torch==2.8.0" "triton>=3.3.0" {_numpy} {_pil} torchvision "torchaudio==2.8.0" bitsandbytes xformers==0.0.32.post2 \\
        "unsloth_zoo[base] @ git+https://github.com/unslothai/unsloth-zoo" \\
        "unsloth[base] @ git+https://github.com/unslothai/unsloth"
    !uv pip install -qqq --no-deps "torchcodec==0.7.0"
elif importlib.util.find_spec("unsloth") is None:
    !uv pip install -qqq unsloth
!uv pip install --upgrade --no-deps "tokenizers>=0.22.0,<=0.23.0" trl==0.22.2 unsloth unsloth_zoo
!uv pip install transformers==5.2.0
!unsloth install-kernels
!uv pip install --no-deps --upgrade "torchao>=0.16.0\""""

RODAPE = """---
### Próximos passos
- `docs/ENGENHARIA-REVERSA.md` explica como cada peça foi reconstruída.
- `docs/AUDITORIA-DE-ROTULOS.md` mostra por que acurácia alta pode esconder erro herdado.
- Abra uma *issue* no repositório se algo quebrar no Colab: as bibliotecas de IA mudam rápido.

*OSINTIA · Deivison Lourenço · MIT*"""


# ---------------------------------------------------------------- 00 núcleo
NB00 = ("00_nucleo_sem_gpu.ipynb", False, [
    ("md", cabecalho("00_nucleo_sem_gpu.ipynb", "00 · O núcleo OSINTIA sem GPU",
        "Antes de treinar qualquer modelo, aprenda a **medir** se ele merece confiança. Este notebook roda só com a biblioteca padrão do Python e usa o caso de demonstração (perfis que imitam o fictício *Banco Aurora*).",
        False, "2 minutos")),
    ("code", SETUP_REPO),
    ("md", "## 1. As perguntas de decisão\nUm modelo de decisão não escreve texto: ele escolhe entre opções definidas antes. Veja o esquema de triagem de perfis e valide contra os limites da API (64 perguntas, 255 opções, 10 níveis)."),
    ("code", """import json
esquema = esquemas.TRIAGEM_PERFIL
print(json.dumps(esquema, indent=2, ensure_ascii=False))
erros, avisos = esquemas.validar(esquema)
print("erros:", erros, "| avisos:", avisos)
print("catálogo disponível:", list(esquemas.CATALOGO))"""),
    ("md", "## 2. O caso de demonstração\nCada linha tem `state` (o perfil em texto), `questions`, `gold` (média de 3 respostas de um **professor** simulado) e `rotulo_humano` (a verificação de um analista). O professor tem um vício proposital: **todo perfil com selo de verificado vira `legitimo`**."),
    ("code", """linhas = dados.carregar_jsonl("/content/OSINTIA/dados/demo/triagem_perfis.jsonl")
print(len(linhas), "perfis")
print(linhas[0]["state"])
print(json.loads(linhas[0]["gold"])["perfil"])
print("humano:", linhas[0]["rotulo_humano"])"""),
    ("md", "## 3. O teto do professor\nSorteamos uma 4ª resposta do professor (fora do gold) e medimos quanto ela concorda com o gold. Esse é o máximo **honesto**: um aluno que passa disso está decorando o professor."),
    ("code", """gold   = dados.rotulos(linhas, "perfil")
humano = [l["rotulo_humano"]["perfil"] for l in linhas]
extra  = [l["amostra_professor_extra"]["perfil"] for l in linhas]

teto = auditoria.teto_do_professor([extra], gold)
print(f"teto do professor:  {teto:.3f}")
print(f"gold x humano:      {auditoria.concordancia(gold, humano):.3f}")
print(f"kappa gold x humano: {auditoria.kappa_cohen(gold, humano):.3f}")
print()
print(auditoria.imprimir_matriz(humano, gold))"""),
    ("md", "## 4. Calibração perfeita, verdade imperfeita\nTratamos as probabilidades do gold como se fossem saídas de um modelo. Contra o próprio gold, a calibração é ótima. Contra o humano, aparece o erro herdado."),
    ("code", """probs = [json.loads(l["gold"])["perfil"]["probabilities"] for l in linhas]
print("vs gold:  ", calibracao.relatorio(probs, gold))
print("vs humano:", calibracao.relatorio(probs, humano))

herdados = auditoria.erros_herdados(gold, gold, humano)
print(f"\\n{len(herdados)} erros que a métrica oficial chamaria de acerto. Exemplo:\\n")
print(linhas[herdados[0]]["state"])"""),
    ("md", "## 5. Temperature scaling\nQuando o modelo é superconfiante, dividir os logits por uma temperatura `T > 1` corrige a confiança sem mudar a decisão. É o que o `FastDecisionModel.calibrate` faz por baixo (reconstrução em `docs/ENGENHARIA-REVERSA.md`)."),
    ("code", """import random
r = random.Random(7)
# modelo de brinquedo superconfiante: diz entre 70% e 99%, mas acerta só 80% do que diz
OPCOES = ("legitimo", "imitador", "bot")
brinquedo, verdade = [], []
for h in humano:
    conf = r.uniform(0.70, 0.99)
    escolha = h if r.random() < conf * 0.80 else r.choice([o for o in OPCOES if o != h])
    p = {o: (1 - conf) / 2 for o in OPCOES}
    p[escolha] = conf
    brinquedo.append(p); verdade.append(h)

antes = calibracao.relatorio(brinquedo, verdade)
T = calibracao.ajustar_temperatura(brinquedo, verdade)
depois = calibracao.relatorio([calibracao.aplicar_temperatura(p, T) for p in brinquedo], verdade)
print("antes: ", antes)
print(f"T = {T:.2f}")
print("depois:", depois)"""),
    ("md", "## 6. Humano no circuito\nEscolha o limiar olhando cobertura (quanto o modelo decide sozinho) contra acurácia automática."),
    ("code", """calibrado = [calibracao.aplicar_temperatura(p, T) for p in brinquedo]
for linha in roteamento.varrer_limiares(calibrado, verdade, limiares=(0.4, 0.5, 0.6, 0.7)):
    print(linha)
print(roteamento.rotear({"legitimo": 0.12, "imitador": 0.81, "bot": 0.07}))"""),
    ("md", "## 7. Extração determinística e LGPD\nRegras com dígito verificador para CPF, CNPJ, telefone e IP. No notebook 02 elas confirmam o que o GLiNER propõe."),
    ("code", """texto = "Chame @suporte_bancoaurora no (31) 99999-0000, envie CPF 529.982.247-25 para estorno@aurora-falso.example"
for e in extracao.extrair(texto):
    print(e)
print(extracao.mascarar(texto))"""),
    ("md", "## 8. Cadeia de custódia\nTodo resultado vira um evento com hash SHA-256 encadeado. Se alguém editar o arquivo depois, a verificação aponta onde."),
    ("code", """import os
os.makedirs("/content/saidas", exist_ok=True)
dados.salvar_jsonl([{"id": l["id"], "decisao": g} for l, g in zip(linhas, gold)], "/content/saidas/decisoes.jsonl")
man = "/content/saidas/manifesto.jsonl"
if os.path.exists(man): os.remove(man)
custodia.registrar(man, "carga_dataset", "/content/OSINTIA/dados/demo/triagem_perfis.jsonl")
custodia.registrar(man, "decisoes", "/content/saidas/decisoes.jsonl", {"teto_professor": round(teto, 4)})
print("problemas:", custodia.verificar(man) or "nenhum, cadeia íntegra")"""),
    ("md", RODAPE),
])

# ---------------------------------------------------------------- 01 decisão
NB01 = ("01_decisao_qwen35_osint.ipynb", True, [
    ("md", cabecalho("01_decisao_qwen35_osint.ipynb", "01 · Modelo de decisão OSINT com Qwen3.5 4B + LoRA",
        "Reconstrução do notebook *Qwen3.5 (4B) Decision* da Unsloth aplicada a OSINT: triagem de perfis imitadores com **probabilidade calibrada** e, o que o original não faz, **auditoria do gabarito** (teto do professor e lacuna humana) antes de confiar no número.",
        True, "15 a 40 min no T4 com o dataset de demonstração (o original leva ~2h com o typed-decisions completo)")),
    ("md", "### Como funciona (resumo da engenharia reversa)\n1. `FastDecisionModel` carrega um LLM normal (Qwen3.5 4B em 4 bits) e **acopla uma cabeça de decisão** pequena que lê todas as perguntas sobre uma entrada em uma passada e pontua cada opção.\n2. LoRA ajusta poucas matrizes do LLM; a cabeça nova sempre treina.\n3. O treino usa gold **suave** (probabilidades), não só o rótulo vencedor.\n4. `calibrate` ajusta as probabilidades no holdout (ECE menor = confiança honesta).\n5. **OSINTIA:** separamos antes um conjunto de auditoria verificado por humano, que nunca entra no treino."),
    ("code", INSTALA_UNSLOTH),
    ("code", SETUP_REPO),
    ("md", "## 1. Carregar o modelo\nTroque `MODELO` por `unsloth/Llama-3.2-3B-Instruct` ou outro suportado se quiser comparar."),
    ("code", """from unsloth import FastDecisionModel, DecisionTrainer, is_bfloat16_supported
import torch

MODELO = "unsloth/Qwen3.5-4B"
model, tokenizer = FastDecisionModel.from_pretrained(
    model_name = MODELO,
    max_seq_length = 2048,
    load_in_4bit = True,
)
model = FastDecisionModel.get_peft_model(
    model,
    r = 16, lora_alpha = 16, lora_dropout = 0,
    use_gradient_checkpointing = "unsloth",
    random_state = 3407,
)"""),
    ("md", "## 2. Dados\n`FONTE` escolhe o que treinar:\n- `\"demo\"`: só a triagem de perfis OSINT (rápido)\n- `\"demo+seguranca\"`: soma o subconjunto `security_incidents` do typed-decisions (mais dados, mais tempo)\n\nPrimeiro separamos **80 perfis de auditoria** com rótulo humano. Eles nunca entram no treino nem na calibração."),
    ("code", """import json
FONTE = "demo"  # ou "demo+seguranca"

linhas = dados.carregar_jsonl("/content/OSINTIA/dados/demo/triagem_perfis.jsonl")
treino_linhas, auditoria_linhas = dados.dividir_holdout(linhas, fracao=0.2, semente=3407)
print(len(treino_linhas), "para treino/calibração |", len(auditoria_linhas), "para auditoria humana")

linhas_treino = [{"state": l["state"], "questions": l["questions"], "gold": l["gold"]} for l in treino_linhas]

if FONTE == "demo+seguranca":
    from datasets import load_dataset
    seg = load_dataset("LocalLLaMA/typed-decisions", "security_incidents", split="train")
    linhas_treino += [{"state": r["state"], "questions": r["questions"], "gold": r["gold"]} for r in seg]

print(len(linhas_treino), "linhas de treino")"""),
    ("md", "Conferindo o formato: o gold oficial do typed-decisions e o nosso têm a mesma estrutura (`label`, `probabilities`, `confidence`, `type`)."),
    ("code", """print(json.dumps(json.loads(linhas_treino[0]["gold"]), indent=2, ensure_ascii=False))"""),
    ("code", """items, report = FastDecisionModel.build_dataset(linhas_treino, tokenizer, model)
print(f"Descartadas {report['skipped']} de {report['total']} decisões")
train_items, eval_items = FastDecisionModel.split_holdout(items, seed = 3407)
print(f"{len(train_items)} para treino, {len(eval_items)} para calibração")
FastDecisionModel.evaluate(model, tokenizer, eval_items)  # antes do treino: perto do chute"""),
    ("md", "## 3. Treinar"),
    ("code", """from transformers import TrainingArguments

trainer = DecisionTrainer(
    model = model,
    processing_class = tokenizer,
    train_dataset = train_items,
    eval_dataset = eval_items,
    args = TrainingArguments(
        per_device_train_batch_size = 8,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        num_train_epochs = 3,      # dataset pequeno: épocas em vez de max_steps
        learning_rate = 2e-4,
        lr_scheduler_type = "cosine",
        weight_decay = 0.01,
        bf16 = is_bfloat16_supported(),
        fp16 = not is_bfloat16_supported(),
        eval_strategy = "epoch",
        logging_steps = 5,
        output_dir = "outputs",
        report_to = "none",
        seed = 3407,
    ),
)
trainer_stats = trainer.train()"""),
    ("md", "## 4. Calibrar no holdout"),
    ("code", """FastDecisionModel.calibrate(model, tokenizer, eval_items)
FastDecisionModel.for_inference(model)"""),
    ("md", "## 5. Auditoria OSINTIA: o modelo aprendeu a tarefa ou o professor?\nRodamos o modelo nos 80 perfis de auditoria e comparamos com o **gold** (professor) e com o **humano**."),
    ("code", """perguntas = esquemas.TRIAGEM_PERFIL
prev, probs = [], []
for l in auditoria_linhas:
    resp = FastDecisionModel.predict(model, tokenizer, l["state"], perguntas)
    prev.append(resp["perfil"]["answer"])
    probs.append(resp["perfil"]["probabilities"])

gold_aud   = dados.rotulos(auditoria_linhas, "perfil")
humano_aud = [l["rotulo_humano"]["perfil"] for l in auditoria_linhas]
extra_aud  = [l["amostra_professor_extra"]["perfil"] for l in auditoria_linhas]

teto = auditoria.teto_do_professor([extra_aud], gold_aud)
print("vs gold:  ", calibracao.relatorio(probs, gold_aud))
print("vs humano:", calibracao.relatorio(probs, humano_aud))
print(f"teto do professor: {teto:.3f}")
print(auditoria.lacuna_humana(prev, gold_aud, humano_aud))
acc_gold = auditoria.concordancia(prev, gold_aud)
if auditoria.alerta_de_decoracao(acc_gold, teto):
    print("⚠️  O modelo concorda com o gold mais do que o próprio professor: está decorando os vícios dele.")"""),
    ("code", """herdados = auditoria.erros_herdados(prev, gold_aud, humano_aud)
print(f"{len(herdados)} erros herdados do professor (a métrica oficial conta como acerto)")
for i in herdados[:3]:
    print("-" * 60)
    print(auditoria_linhas[i]["state"])
    print("modelo:", prev[i], {k: round(v, 3) for k, v in probs[i].items()}, "| humano:", humano_aud[i])"""),
    ("md", "## 6. Escolher o limiar de revisão humana"),
    ("code", """for linha in roteamento.varrer_limiares(probs, humano_aud):
    print(linha)"""),
    ("md", "## 7. Decidir um perfil novo\nAs perguntas podem misturar `choice`, `noul` e `score`. A pergunta `pede_dados` não estava no treino: a cabeça de decisão lê a instrução, mas a qualidade em tipos não treinados é menor. Para produção, inclua exemplos rotulados de cada pergunta que vai usar."),
    ("code", """novo = \"\"\"Alvo monitorado: @bancoaurora
Perfil analisado: @bancoaurora.suporte24h
Selo de verificado: sim
Conta criada há 6 dias
Seguidores: 312
Média de postagens por dia: 9.5
Bio: Central de estorno. Mande seu CPF e o código recebido por SMS no direct.
Link na bio: https://aurora-estorno.example
Conteúdo repetido entre postagens: sim\"\"\"

perguntas_novas = dict(esquemas.TRIAGEM_PERFIL)
perguntas_novas["pede_dados"] = {"type": "noul", "instructions": "O perfil pede dados pessoais, senha ou código?"}

resp = FastDecisionModel.predict(model, tokenizer, novo, perguntas_novas)
for nome, r in resp.items():
    print(nome, r["answer"], {k: round(v, 3) for k, v in r["probabilities"].items()})
print("encaminhamento:", roteamento.rotear(resp["perfil"]["probabilities"], limiar=0.75))"""),
    ("md", "## 8. Registrar e salvar"),
    ("code", """import os
os.makedirs("/content/saidas", exist_ok=True)
dados.salvar_jsonl(
    [{"id": l["id"], "previsto": p, "probabilidades": pr, "humano": h} for l, p, pr, h in zip(auditoria_linhas, prev, probs, humano_aud)],
    "/content/saidas/auditoria_decisao.jsonl",
)
custodia.registrar("/content/saidas/manifesto.jsonl", "auditoria_modelo_decisao",
                   "/content/saidas/auditoria_decisao.jsonl", {"modelo": MODELO, "teto": round(teto, 4)})

model.save_pretrained("osintia_decisao_lora")  # LoRA + cabeça de decisão + calibração
# model.push_to_hub("seu_usuario/osintia_decisao_lora", token = "SEU_TOKEN_HF")"""),
    ("md", RODAPE),
])

# ---------------------------------------------------------------- 02 GLiNER
NB02 = ("02_gliner_entidades_pii.ipynb", False, [
    ("md", cabecalho("02_gliner_entidades_pii.ipynb", "02 · Entidades e PII com GLiNER + validação brasileira",
        "O **GLiNER** extrai entidades de qualquer tipo que você nomear, sem treino (zero-shot), e roda até em CPU. O OSINTIA soma a ele validadores determinísticos brasileiros (CPF, CNPJ, DDD, IP público) e monta um **grafo de coocorrência** para análise de vínculos.",
        False, "5 minutos (CPU) · 1 minuto (GPU)")),
    ("code", "!pip install -q gliner"),
    ("code", SETUP_REPO),
    ("md", "## 1. Carregar o modelo\n- `urchade/gliner_multi-v2.1`: multilíngue, bom em português, Apache-2.0\n- `urchade/gliner_multi_pii-v1`: afinado para dados pessoais"),
    ("code", """from gliner import GLiNER
MODELO = "urchade/gliner_multi-v2.1"
modelo = GLiNER.from_pretrained(MODELO)"""),
    ("md", "## 2. Textos de exemplo (fictícios)"),
    ("code", """textos = {
    "post_golpe": "Atenção clientes do Banco Aurora! Problemas com estorno? Fale com Marcos Vieira no WhatsApp (31) 99999-0000 ou mande e-mail para estorno@aurora-falso.example. Pix para a chave 529.982.247-25 libera em 1h.",
    "paste": "dump aurora_rh 2026: joana.prado@aurora.example ; carlos.m@aurora.example ; servidor 200.160.2.3 ; painel http://10.0.0.15/admin ; CNPJ 11.222.333/0001-81",
    "forum": "o @bancoaur0ra e o @suporte_bancoaurora sao do mesmo cara, usam a mesma carteira bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh e postam de Belo Horizonte",
}
ROTULOS = ["pessoa", "organização", "local", "telefone", "e-mail", "username de rede social",
           "carteira de criptomoeda", "endereço IP", "URL", "documento CPF ou CNPJ"]"""),
    ("md", "## 3. Extrair com GLiNER e confirmar com regras\nO modelo propõe pelo contexto; a regra confirma o formato e o dígito verificador."),
    ("code", """MAPA = {"telefone": "telefone", "e-mail": "email", "endereço IP": "ip", "documento CPF ou CNPJ": ("cpf", "cnpj")}

def confirmar(rotulo, valor):
    alvo = MAPA.get(rotulo)
    if not alvo:
        return None  # sem regra para esse tipo: fica só a confiança do modelo
    alvos = alvo if isinstance(alvo, tuple) else (alvo,)
    regra = [e for e in extracao.extrair(valor) if e["tipo"] in alvos]
    return bool(regra) and all(e["valido"] for e in regra)

tabela = []
for doc, texto in textos.items():
    for ent in modelo.predict_entities(texto, ROTULOS, threshold=0.4):
        tabela.append({
            "doc": doc, "rotulo": ent["label"], "valor": ent["text"],
            "score": round(ent["score"], 3), "regra_confirma": confirmar(ent["label"], ent["text"]),
        })

for t in tabela:
    print(t)"""),
    ("md", "## 4. O que o modelo deixou passar?\nAs regras rodam no texto inteiro. Tudo que a regra achou e o modelo não, vale revisar."),
    ("code", """for doc, texto in textos.items():
    achados_modelo = {t["valor"] for t in tabela if t["doc"] == doc}
    for e in extracao.extrair(texto):
        if not any(e["valor"] in v or v in e["valor"] for v in achados_modelo):
            print(doc, "->", e["tipo"], e["valor"], "| válido:", e["valido"])"""),
    ("md", "## 5. Grafo de coocorrência\nEntidades no mesmo documento ganham uma aresta. É a semente de uma análise de vínculos (exporte para Gephi, Maltego ou o VINCULA)."),
    ("code", """import csv, itertools, os
from collections import Counter

arestas = Counter()
for doc in textos:
    ents = sorted({(t["rotulo"], t["valor"]) for t in tabela if t["doc"] == doc})
    for a, b in itertools.combinations(ents, 2):
        arestas[(a, b)] += 1

os.makedirs("/content/saidas", exist_ok=True)
with open("/content/saidas/vinculos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["origem_tipo", "origem", "destino_tipo", "destino", "peso"])
    for (a, b), peso in arestas.items():
        w.writerow([a[0], a[1], b[0], b[1], peso])
print(len(arestas), "arestas em /content/saidas/vinculos.csv")"""),
    ("md", "## 6. Relatório com LGPD\nPara compartilhar, mascare identificadores pessoais e registre a cadeia de custódia."),
    ("code", """for doc, texto in textos.items():
    print(doc, "->", extracao.mascarar(texto))
custodia.registrar("/content/saidas/manifesto.jsonl", "extracao_gliner", "/content/saidas/vinculos.csv", {"modelo": MODELO})"""),
    ("md", RODAPE),
])

# ---------------------------------------------------------------- 03 DeepSeek ACH
NB03 = ("03_deepseek_r1_ach.ipynb", True, [
    ("md", cabecalho("03_deepseek_r1_ach.ipynb", "03 · Análise de Hipóteses Concorrentes (ACH) com DeepSeek-R1",
        "O **DeepSeek-R1-Distill-Qwen-7B** é um modelo de raciocínio que cabe no T4 em 4 bits. Aqui ele preenche a matriz de **ACH** (Heuer) sobre um caso fictício. A inovação: rodamos o raciocínio **várias vezes** e medimos a consistência de cada célula, a mesma lógica do teto do professor aplicada ao raciocínio.",
        True, "10 a 20 minutos")),
    ("code", "!pip install -q -U transformers accelerate bitsandbytes"),
    ("code", SETUP_REPO),
    ("md", "## 1. Carregar o modelo em 4 bits\nSem GPU grande? Troque por `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`."),
    ("code", """import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

MODELO = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
tok = AutoTokenizer.from_pretrained(MODELO)
llm = AutoModelForCausalLM.from_pretrained(
    MODELO,
    device_map = "auto",
    quantization_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16),
)"""),
    ("md", "## 2. O caso (fictício)\nCampanha de perfis imitando o Banco Aurora. Quatro hipóteses, seis evidências."),
    ("code", """HIPOTESES = {
    "H1": "Golpistas oportunistas independentes",
    "H2": "Grupo organizado coordenando a campanha",
    "H3": "Teste autorizado de red team contratado pelo banco",
    "H4": "Perfis criados por erro interno do próprio banco",
}
EVIDENCIAS = {
    "E1": "12 perfis criados no mesmo intervalo de 48 horas",
    "E2": "Todos usam a mesma chave Pix para receber pagamentos",
    "E3": "As bios têm erros de português idênticos",
    "E4": "O banco nega ter contratado testes nesse período",
    "E5": "Vítimas relatam prejuízo real de dinheiro",
    "E6": "Três perfis compraram selo de verificado",
}"""),
    ("md", "## 3. Pedir a matriz ACH em JSON\nRecomendação dos autores do R1: sem *system prompt*, instruções na mensagem do usuário, temperatura ~0.6. O raciocínio vem entre `<think>` e `</think>`; guardamos, mas a decisão sai do JSON."),
    ("code", """import json, re

ESCALA = {"CC": 2, "C": 1, "N": 0, "I": -1, "II": -2}

def montar_prompt():
    h = "\\n".join(f"{k}: {v}" for k, v in HIPOTESES.items())
    e = "\\n".join(f"{k}: {v}" for k, v in EVIDENCIAS.items())
    return f\"\"\"Você é analista de inteligência e aplica Análise de Hipóteses Concorrentes (ACH).
Hipóteses:
{h}
Evidências:
{e}
Para cada evidência e hipótese, classifique: CC (muito consistente), C (consistente), N (neutra), I (inconsistente), II (muito inconsistente).
Responda ao final apenas com JSON no formato {{"E1": {{"H1": "C", "H2": "CC", ...}}, ...}}.\"\"\"

def perguntar(prompt, temperatura=0.6, max_tokens=2048):
    msgs = [{"role": "user", "content": prompt}]
    entrada = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt").to(llm.device)
    saida = llm.generate(entrada, max_new_tokens=max_tokens, do_sample=True, temperature=temperatura, top_p=0.95)
    return tok.decode(saida[0][entrada.shape[1]:], skip_special_tokens=True)

def separar(resposta):
    raciocinio, _, final = resposta.partition("</think>")
    if not final:
        final, raciocinio = raciocinio, ""
    blocos = re.findall(r"\\{.*\\}", final, flags=re.S)
    matriz = json.loads(blocos[-1]) if blocos else None
    return raciocinio.strip(), matriz"""),
    ("md", "## 4. Rodar várias vezes (autoconsistência)"),
    ("code", """RODADAS = 3
matrizes, raciocinios = [], []
for i in range(RODADAS):
    raciocinio, matriz = separar(perguntar(montar_prompt()))
    if matriz:
        matrizes.append(matriz); raciocinios.append(raciocinio)
    print(f"rodada {i + 1}: {'ok' if matriz else 'sem JSON válido'}")"""),
    ("md", "## 5. Pontuar como Heuer\nNa ACH a hipótese mais forte é a com **menos inconsistência**, não a com mais apoio. Somamos só os pesos negativos."),
    ("code", """from collections import Counter

def inconsistencia(matriz):
    return {h: sum(min(ESCALA.get(matriz.get(e, {}).get(h, "N"), 0), 0) for e in EVIDENCIAS) for h in HIPOTESES}

for i, m in enumerate(matrizes, 1):
    print(f"rodada {i}:", dict(sorted(inconsistencia(m).items(), key=lambda x: x[1], reverse=True)))

consistencia = {}
for e in EVIDENCIAS:
    for h in HIPOTESES:
        votos = Counter(m.get(e, {}).get(h, "N") for m in matrizes)
        rotulo, n = votos.most_common(1)[0]
        consistencia[(e, h)] = (rotulo, n / len(matrizes))

instaveis = [(k, v) for k, v in consistencia.items() if v[1] < 1]
print(f"\\n{len(instaveis)} de {len(consistencia)} células mudaram entre rodadas:")
for (e, h), (rot, frac) in instaveis:
    print(f"  {e} x {h}: maioria {rot} em {frac:.0%}")"""),
    ("md", "### Leitura\n- Células instáveis são onde o modelo **não sabe**: leve essas para o analista.\n- O raciocínio em `<think>` é útil para entender o modelo, mas **não é evidência**. Nunca cite como fonte."),
    ("code", """import os
os.makedirs("/content/saidas", exist_ok=True)
with open("/content/saidas/ach.json", "w", encoding="utf-8") as f:
    json.dump({"modelo": MODELO, "matrizes": matrizes, "raciocinios": raciocinios}, f, ensure_ascii=False, indent=2)
custodia.registrar("/content/saidas/manifesto.jsonl", "ach_deepseek", "/content/saidas/ach.json", {"rodadas": RODADAS})"""),
    ("md", RODAPE),
])

# ---------------------------------------------------------------- 04 embeddings
NB04 = ("04_embeddings_vinculos.ipynb", False, [
    ("md", cabecalho("04_embeddings_vinculos.ipynb", "04 · Embeddings para resolução de entidades e comportamento coordenado",
        "Com o **multilingual-e5** transformamos bios e postagens em vetores. Isso permite achar contas que provavelmente são da mesma pessoa e textos quase idênticos espalhados por várias contas (sinal de comportamento inautêntico coordenado). Combinamos com similaridade de username, a mesma ideia do SÓSIA.",
        False, "3 minutos (CPU)")),
    ("code", "!pip install -q sentence-transformers"),
    ("code", SETUP_REPO),
    ("code", """from sentence_transformers import SentenceTransformer
MODELO = "intfloat/multilingual-e5-base"
enc = SentenceTransformer(MODELO)

linhas = dados.carregar_jsonl("/content/OSINTIA/dados/demo/triagem_perfis.jsonl")
def campo(state, nome):
    for l in state.splitlines():
        if l.startswith(nome):
            return l.split(":", 1)[1].strip()
    return ""
perfis = [{"id": l["id"], "user": campo(l["state"], "Perfil analisado").lstrip("@"),
           "bio": campo(l["state"], "Bio"), "link": campo(l["state"], "Link na bio"),
           "humano": l["rotulo_humano"]["perfil"]} for l in linhas[:120]]
print(len(perfis), "perfis")"""),
    ("md", "## 1. Vetores\nO e5 pede o prefixo `query: ` (ou `passage: `). `normalize_embeddings=True` deixa o produto escalar igual ao cosseno."),
    ("code", """vet = enc.encode(["query: " + p["bio"] for p in perfis], normalize_embeddings=True)
sim = vet @ vet.T
print(sim.shape)"""),
    ("md", "## 2. Pontuação de vínculo entre contas\n`0.5 × bio + 0.3 × username + 0.2 × mesmo domínio`. Os pesos são um ponto de partida; ajuste com casos reais."),
    ("code", """from difflib import SequenceMatcher
from urllib.parse import urlparse

def dominio(url):
    return urlparse(url).netloc.lower()

def vinculo(i, j):
    a, b = perfis[i], perfis[j]
    s_user = SequenceMatcher(None, a["user"], b["user"]).ratio()
    s_dom = 1.0 if dominio(a["link"]) == dominio(b["link"]) else 0.0
    return 0.5 * float(sim[i, j]) + 0.3 * s_user + 0.2 * s_dom

pares = sorted(((vinculo(i, j), i, j) for i in range(len(perfis)) for j in range(i + 1, len(perfis))
                if perfis[i]["user"] != perfis[j]["user"]), reverse=True)
for s, i, j in pares[:10]:
    print(f"{s:.3f}  @{perfis[i]['user']:<28} @{perfis[j]['user']:<28} ({perfis[i]['humano']}/{perfis[j]['humano']})")"""),
    ("md", "## 3. Agrupar contas (union-find, só stdlib)"),
    ("code", """LIMIAR = 0.80
pai = list(range(len(perfis)))
def raiz(x):
    while pai[x] != x:
        pai[x] = pai[pai[x]]; x = pai[x]
    return x
for s, i, j in pares:
    if s < LIMIAR: break
    pai[raiz(i)] = raiz(j)

from collections import defaultdict
grupos = defaultdict(set)
for i, p in enumerate(perfis):
    grupos[raiz(i)].add(p["user"])
grupos = sorted((g for g in grupos.values() if len(g) > 1), key=len, reverse=True)
for g in grupos[:5]:
    print(len(g), sorted(g))"""),
    ("md", "## 4. Distância do alvo oficial\nQuanto mais parecido com `@bancoaurora` sem ser ele, mais suspeito."),
    ("code", """ALVO = "bancoaurora"
suspeitos = sorted({p["user"] for p in perfis if p["user"] != ALVO},
                   key=lambda u: SequenceMatcher(None, ALVO, u).ratio(), reverse=True)
for u in suspeitos[:10]:
    print(f"{SequenceMatcher(None, ALVO, u).ratio():.2f}  @{u}")"""),
    ("code", """import json, os
os.makedirs("/content/saidas", exist_ok=True)
with open("/content/saidas/grupos.json", "w", encoding="utf-8") as f:
    json.dump([sorted(g) for g in grupos], f, ensure_ascii=False, indent=2)
custodia.registrar("/content/saidas/manifesto.jsonl", "resolucao_entidades", "/content/saidas/grupos.json", {"modelo": MODELO, "limiar": LIMIAR})"""),
    ("md", RODAPE),
])

# ---------------------------------------------------------------- 05 visão
NB05 = ("05_qwen35_visao_geoint.ipynb", True, [
    ("md", cabecalho("05_qwen35_visao_geoint.ipynb", "05 · Pistas de GEOINT em imagens com Qwen3.5 4B (visão)",
        "O Qwen3.5 é um modelo unificado de texto e visão. Aqui ele **descreve pistas** de localização (idioma de placas, arquitetura, vegetação, clima, veículos) em JSON estruturado. Ele não dá a resposta final: as pistas guiam o analista, que confirma com fontes como mapas e imagens de satélite. Também extraímos o EXIF com Pillow.",
        True, "10 minutos")),
    ("code", INSTALA_UNSLOTH),
    ("code", SETUP_REPO),
    ("code", """from unsloth import FastVisionModel
MODELO = "unsloth/Qwen3.5-4B"
model, tokenizer = FastVisionModel.from_pretrained(MODELO, load_in_4bit=True)
FastVisionModel.for_inference(model)"""),
    ("md", "## 1. Envie uma imagem\nUse uma imagem que você tem direito de analisar. Fotos enviadas para redes sociais costumam perder o EXIF; arquivos originais não."),
    ("code", """from google.colab import files
from PIL import Image
enviado = files.upload()
caminho = next(iter(enviado))
imagem = Image.open(caminho).convert("RGB")
imagem.thumbnail((1024, 1024))
imagem"""),
    ("md", "## 2. EXIF (metadados)"),
    ("code", """from PIL.ExifTags import TAGS, GPSTAGS
bruto = Image.open(caminho).getexif()
exif = {TAGS.get(k, k): v for k, v in bruto.items()}
gps = {GPSTAGS.get(k, k): v for k, v in bruto.get_ifd(0x8825).items()} if bruto else {}
print({k: exif[k] for k in ("Make", "Model", "DateTime", "Software") if k in exif})
print("GPS:", gps or "sem GPS no arquivo")"""),
    ("md", "## 3. Pistas estruturadas"),
    ("code", """import json, re
from transformers import TextStreamer

PEDIDO = \"\"\"Analise a imagem como um analista de GEOINT. Não chute a localização final.
Responda só com JSON neste formato:
{"idioma_textos": [], "textos_legiveis": [], "arquitetura": "", "vegetacao": "", "clima_estacao": "",
 "veiculos_e_mao_de_direcao": "", "infraestrutura": "", "paises_candidatos": [], "proximos_passos": []}\"\"\"

msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PEDIDO}]}]
texto = tokenizer.apply_chat_template(msgs, add_generation_prompt=True)
entradas = tokenizer(imagem, texto, add_special_tokens=False, return_tensors="pt").to("cuda")
saida = model.generate(**entradas, max_new_tokens=700, use_cache=True, temperature=0.3, min_p=0.1)
resposta = tokenizer.decode(saida[0][entradas["input_ids"].shape[1]:], skip_special_tokens=True)
blocos = re.findall(r"\\{.*\\}", resposta, flags=re.S)
pistas = json.loads(blocos[-1]) if blocos else {"bruto": resposta}
print(json.dumps(pistas, indent=2, ensure_ascii=False))"""),
    ("md", "### Leitura\n- Textos legíveis e idioma são as pistas mais fortes; vegetação e arquitetura apenas restringem.\n- `paises_candidatos` é hipótese, não conclusão. Confirme cada uma.\n- Modelos de visão podem **inventar texto** que não está na imagem: confira os `textos_legiveis` olhando a foto."),
    ("code", """import hashlib, os
os.makedirs("/content/saidas", exist_ok=True)
with open("/content/saidas/geoint.json", "w", encoding="utf-8") as f:
    json.dump({"arquivo": caminho, "exif": {k: str(v) for k, v in exif.items()}, "gps": {k: str(v) for k, v in gps.items()},
               "pistas": pistas, "modelo": MODELO}, f, ensure_ascii=False, indent=2)
custodia.registrar("/content/saidas/manifesto.jsonl", "coleta_imagem", caminho)
custodia.registrar("/content/saidas/manifesto.jsonl", "pistas_geoint", "/content/saidas/geoint.json", {"modelo": MODELO})"""),
    ("md", RODAPE),
])

# ---------------------------------------------------------------- 06 reconstrução mínima
NB06 = ("06_decisao_sem_unsloth.ipynb", True, [
    ("md", cabecalho("06_decisao_sem_unsloth.ipynb", "06 · Reconstrução mínima: modelo de decisão só com transformers",
        "Engenharia reversa da ideia, sem a pilha da Unsloth: em vez de gerar texto, medimos a **probabilidade de cada opção** como continuação da pergunta, normalizamos com softmax e calibramos com *temperature scaling* do núcleo OSINTIA. É *zero-shot* (sem treino) e serve de linha de base para comparar com o notebook 01.",
        True, "5 a 10 minutos (T4) · funciona em CPU, mais devagar")),
    ("code", '!pip install -q -U "transformers>=4.45" accelerate'),
    ("code", SETUP_REPO),
    ("md", "## 1. Um LLM pequeno e comum\nQualquer modelo de chat serve. `Qwen/Qwen2.5-1.5B-Instruct` é leve e entende português."),
    ("code", """import math, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODELO = "Qwen/Qwen2.5-1.5B-Instruct"
tok = AutoTokenizer.from_pretrained(MODELO)
lm = AutoModelForCausalLM.from_pretrained(MODELO, torch_dtype="auto", device_map="auto")
lm.eval()"""),
    ("md", "## 2. A cabeça de decisão, versão artesanal\nPara cada opção, somamos o log da probabilidade dos tokens do nome da opção depois do prompt. As opções viram uma distribuição. Nada é gerado."),
    ("code", """def montar_prompt(state, pergunta):
    linhas = "\\n".join(f"- {o}: {d}" for o, d in pergunta["criteria"].items())
    texto = f"{state}\\n\\nPergunta: {pergunta['instructions']}\\nOpções:\\n{linhas}\\nResponda só com o nome exato de uma opção."
    return tok.apply_chat_template([{"role": "user", "content": texto}], add_generation_prompt=True, tokenize=False)

@torch.no_grad()
def decidir(state, pergunta):
    base = montar_prompt(state, pergunta)
    n_base = len(tok(base, add_special_tokens=False)["input_ids"])
    pontos = {}
    for opcao in pergunta["criteria"]:
        ids = tok(base + opcao, add_special_tokens=False, return_tensors="pt")["input_ids"].to(lm.device)
        logp = torch.log_softmax(lm(ids).logits[0, :-1].float(), dim=-1)
        alvo = ids[0, 1:]
        pontos[opcao] = logp[n_base - 1:, :].gather(1, alvo[n_base - 1:, None]).sum().item()
    maior = max(pontos.values())
    expo = {o: math.exp(v - maior) for o, v in pontos.items()}
    soma = sum(expo.values())
    return {o: v / soma for o, v in expo.items()}

print(decidir("Perfil analisado: @bancoaur0ra\\nBio: Mande seu CPF no direct para estorno.", esquemas.TRIAGEM_PERFIL["perfil"]))"""),
    ("md", "## 3. Calibrar e auditar\nMesma divisão do notebook 01: auditoria humana separada; calibração em outra parte."),
    ("code", """linhas = dados.carregar_jsonl("/content/OSINTIA/dados/demo/triagem_perfis.jsonl")
resto, aud = dados.dividir_holdout(linhas, fracao=0.2, semente=3407)
calib = resto[:80]
pergunta = esquemas.TRIAGEM_PERFIL["perfil"]

p_calib = [decidir(l["state"], pergunta) for l in calib]
T = calibracao.ajustar_temperatura(p_calib, dados.rotulos(calib, "perfil"))
print(f"temperatura = {T:.2f}")

p_aud = [calibracao.aplicar_temperatura(decidir(l["state"], pergunta), T) for l in aud]
gold_aud = dados.rotulos(aud, "perfil")
humano_aud = [l["rotulo_humano"]["perfil"] for l in aud]
prev = [max(p, key=p.get) for p in p_aud]
print("vs gold:  ", calibracao.relatorio(p_aud, gold_aud))
print("vs humano:", calibracao.relatorio(p_aud, humano_aud))
print(auditoria.lacuna_humana(prev, gold_aud, humano_aud))"""),
    ("md", "### O que comparar com o notebook 01\n- O zero-shot costuma errar mais, mas **não herda o vício do professor**, porque nunca viu o gold. Se ele concordar mais com o humano do que o modelo treinado, o problema está no rótulo, não no modelo.\n- Cada opção custa uma passada do modelo; a cabeça da Unsloth pontua todas as perguntas numa passada só. É aí que mora o ganho de velocidade."),
    ("code", """import os
os.makedirs("/content/saidas", exist_ok=True)
dados.salvar_jsonl([{"id": l["id"], "probabilidades": p} for l, p in zip(aud, p_aud)], "/content/saidas/zero_shot.jsonl")
custodia.registrar("/content/saidas/manifesto.jsonl", "decisao_zero_shot", "/content/saidas/zero_shot.jsonl", {"modelo": MODELO, "T": round(T, 3)})"""),
    ("md", RODAPE),
])

NOTEBOOKS = [NB00, NB01, NB02, NB03, NB04, NB05, NB06]


def celula(tipo, fonte):
    linhas = fonte.split("\n")
    fonte_lista = [l + "\n" for l in linhas[:-1]] + [linhas[-1]]
    if tipo == "md":
        return {"cell_type": "markdown", "metadata": {}, "source": fonte_lista}
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": fonte_lista}


def construir(nome, gpu, celulas):
    meta = {
        "colab": {"provenance": [], "name": nome},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    }
    if gpu:
        meta["accelerator"] = "GPU"
        meta["colab"]["gpuType"] = "T4"
    return {"nbformat": 4, "nbformat_minor": 0, "metadata": meta, "cells": [celula(t, f) for t, f in celulas]}


def main():
    os.makedirs(PASTA, exist_ok=True)
    for nome, gpu, celulas in NOTEBOOKS:
        caminho = os.path.join(PASTA, nome)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(construir(nome, gpu, celulas), f, ensure_ascii=False, indent=1)
            f.write("\n")
        print(f"{nome}: {len(celulas)} células")


if __name__ == "__main__":
    main()
