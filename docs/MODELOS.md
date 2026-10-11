# Fichas dos modelos

Verifique sempre a licença no cartão do modelo antes de uso comercial ou em investigações com consequências legais. Os valores de memória são aproximados.

| Modelo | Notebook | Tipo | Tamanho | Memória aproximada | Português | Observações |
|---|---|---|---|---|---|---|
| `unsloth/Qwen3.5-4B` (decisão) | 01 | LLM + cabeça de decisão (LoRA) | 4B | cabe no T4 em 4 bits; treino em float32 no T4 | Sim | No T4 o treino é lento porque o Qwen3.5 dá NaN em float16 |
| `unsloth/Qwen3.5-4B` (visão) | 05 | Modelo unificado texto + visão | 4B | ~10 GB em LoRA bf16, menos em 4 bits | Sim | Pode inventar texto que não está na imagem |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 03 | Raciocínio (destilado do R1) | 7B | ~5–6 GB em 4 bits | Razoável | Sem *system prompt*; temperatura ~0,6; raciocínio em `<think>` |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 03 (alternativa) | Raciocínio | 1,5B | ~2 GB | Fraco | Para testes rápidos |
| `urchade/gliner_multi-v2.1` | 02 | NER zero-shot (encoder) | ~0,2B | CPU | Sim | Rótulos livres; Apache-2.0 |
| `urchade/gliner_multi_pii-v1` | 02 (alternativa) | NER de dados pessoais | ~0,2B | CPU | Sim | Afinado para PII |
| `intfloat/multilingual-e5-base` | 04 | Embeddings de sentença | ~0,3B | CPU | Sim | Exige prefixo `query: ` ou `passage: ` |
| `Qwen/Qwen2.5-1.5B-Instruct` | 06 | LLM de chat | 1,5B | ~3 GB | Sim | Linha de base *zero-shot* |
| `geoclip` (GeoCLIP, NeurIPS 2023) | 08 | Geolocalização imagem → GPS (contrastivo, estilo CLIP) | encoder CLIP + encoder de localização | T4 ou CPU | — | Devolve top-k coordenadas; a probabilidade é relativa à galeria e não vem calibrada |
| `geolocal/StreetCLIP` | 08 (opcional) | Zero-shot país/cidade entre candidatos | base `clip-vit-large-patch14-336` | T4 ou CPU | — | **CC BY-NC 4.0**; viés ocidental; sem Índia e China; imagens privadas fora de escopo |

## Ferramentas de coleta (sem IA)

| Ferramenta | Notebook | O que faz | Licença |
|---|---|---|---|
| crt.sh | 07 | Busca em logs de Certificate Transparency (stdlib, `osintia.coleta`) | serviço público |
| Wayback Machine CDX | 07 | Capturas históricas; extração de IDs de analytics (stdlib) | serviço público |
| [Maigret](https://github.com/soxoj/maigret) | 07 | Perfis públicos por username em milhares de sites | MIT |
| [Holehe](https://github.com/megadose/holehe) | 07 (opcional) | Serviços onde um e-mail tem conta | GPL-3.0 |
| [coordination-network-toolkit](https://pypi.org/project/coordination-network-toolkit) | 09 (opcional) | Redes de coordenação; o método está reimplementado em `osintia.coordenacao` | MIT |

## No radar (não usados ainda)

- **Laya / Clef** (Unsloth): modelos de decisão baseados em *encoder*, servidos localmente pela API `/v1/systemone`. A versão multilíngue cobre mais de 100 idiomas com contexto de 1.024 tokens; a de *typed decisions* é só em inglês. Bons candidatos para triagem em CPU.
- **GLiNER2-PII**: modelo multilíngue de ~0,3B para dados pessoais, descrito pela Pioneer AI em 2026. Vale testar contra o `gliner_multi_pii-v1` em português.
- **Qwen3.5 0.8B e 2B**: mesmos notebooks, menos memória. Úteis para comparar se a cabeça de decisão compensa um modelo menor.

## Dataset de referência

| Dataset | Uso | Tamanho | Licença | Cuidado |
|---|---|---|---|---|
| `LocalLLaMA/typed-decisions` | Notebook 01 (opcional, subconjunto `security_incidents`) | 1,6 mil linhas, 4 domínios | Apache-2.0 | Gold gerado por modelo; veja `AUDITORIA-DE-ROTULOS.md` |
| `dados/demo/triagem_perfis.jsonl` | 00, 01, 04, 06 | 400 linhas | MIT | Sintético e fictício |
| `dados/demo/campanha_coordenada.csv` | 09 | 301 mensagens, 81 contas | MIT | Sintético; inclui a armadilha da imprensa |
| `dados/demo/geo_previsoes.jsonl` | 08 | 240 previsões top-5 | MIT | Sintético; geolocalizador superconfiante |
