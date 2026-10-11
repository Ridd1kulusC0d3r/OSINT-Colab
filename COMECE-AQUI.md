# Comece aqui

Você não precisa instalar nada para começar. Escolha um caminho.

## Caminho 1 · Só no navegador (recomendado)

1. Abra o [notebook 00 no Colab](https://colab.research.google.com/github/Ridd1kulusC0d3r/OSINT-Colab/blob/main/notebooks/00_nucleo_sem_gpu.ipynb).
2. Menu **Ambiente de execução → Executar tudo**.
3. Em 2 minutos você verá o teto do professor, a calibração e a cadeia de custódia funcionando.

Depois, para os modelos de IA:

4. Abra o [notebook 01](https://colab.research.google.com/github/Ridd1kulusC0d3r/OSINT-Colab/blob/main/notebooks/01_decisao_qwen35_osint.ipynb).
5. Menu **Ambiente de execução → Alterar o tipo de ambiente de execução → T4 GPU → Salvar**.
6. **Executar tudo** e espere a instalação (5 a 10 minutos) e o treino.

## Caminho 2 · No seu computador (só o núcleo)

Precisa de Python 3.9 ou mais novo ([python.org](https://www.python.org/downloads/)).

1. Baixe o repositório: botão verde **Code → Download ZIP** e descompacte.
2. Dê dois cliques no lançador do seu sistema:
   - Windows: `rodar-no-windows.bat`
   - macOS: `rodar-no-mac.command` (na primeira vez: botão direito → Abrir)
   - Linux: `rodar-no-linux.sh` (ou `bash rodar-no-linux.sh` no terminal)
3. O lançador roda os 43 testes, a auditoria do caso de demonstração e a detecção de coordenação.

## Qual notebook usar?

| Eu quero... | Notebook |
|---|---|
| Entender se posso confiar num modelo | 00 |
| Triar perfis, IOCs, fontes ou postagens com probabilidade | 01 |
| Extrair nomes, telefones, CPFs e e-mails de textos | 02 |
| Comparar hipóteses de um caso | 03 |
| Descobrir contas da mesma pessoa ou campanhas coordenadas | 04 |
| Tirar pistas de localização de uma foto | 05 |
| Ter uma linha de base sem treino | 06 |
| Coletar contas, domínios e IDs de analytics a partir de uma marca | 07 |
| Estimar coordenadas de uma foto e saber quanto confiar | 08 |
| Encontrar contas que agem em conjunto (campanhas) | 09 |
| Ver outros notebooks de OSINT da comunidade | `docs/COLABS-RELACIONADOS.md` |

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `CUDA out of memory` | Confirme que escolheu T4. Reinicie o ambiente. No notebook 03, troque para o modelo 1.5B. |
| Instalação falha no notebook 01 ou 05 | As versões da Unsloth mudam rápido. Compare com o notebook oficial mais recente e abra uma *issue*. |
| `ModuleNotFoundError: osintia` | Rode a célula que baixa o repositório (a segunda de cada notebook). |
| crt.sh ou Wayback não respondem (notebook 07) | Serviços públicos ficam lentos às vezes. O notebook segue sem eles; rode a célula de novo mais tarde. |
| Treino muito lento no T4 | Normal: o Qwen3.5 treina em float32 no T4. Use o dataset `demo` (padrão). |

Manual completo e ilustrado: [docs/manual.html](docs/manual.html) (baixe e abra no navegador).
