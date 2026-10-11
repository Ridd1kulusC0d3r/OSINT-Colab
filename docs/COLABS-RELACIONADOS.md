# Colabs e ferramentas relacionadas

Notebooks e projetos abertos que seguem a mesma proposta do OSINTIA: investigação em fontes abertas rodando direto no navegador. Levantamento feito em 11/10/2026. **Nenhum deles foi executado para esta lista**: as descrições vêm dos próprios repositórios e cartões de modelo. Confira licença e manutenção antes de usar num caso.

Legenda de encaixe: **07** coleta · **01** triagem · **04** vínculos · **05/08** geolocalização · **09** coordenação.

## Bellingcat · Open Source Research Notebooks

Repositório: [bellingcat/open-source-research-notebooks](https://github.com/bellingcat/open-source-research-notebooks) · guia: [How Code Notebooks Enable Open Source Research](https://www.bellingcat.com/resources/2024/03/06/how-code-notebooks-enable-open-source-research/)

A referência do gênero, mantida por quem faz investigação de verdade. Cada notebook tem botão para o Colab.

| Notebook | Nível | O que faz | IA | Encaixe |
|---|---|---|---|---|
| Telegram Phone Number Checker | fácil | Verifica se telefones têm conta no Telegram | — | 07 |
| Wayback Google Analytics | fácil | IDs históricos de analytics via Wayback Machine | — | 07 (reimplementado em `coleta.historico_analytics`) |
| Geoclustering | médio | Agrupa incidentes de um CSV no mapa | clustering | 08 |
| vk-url-scraper | médio | Coleta dados e mídia do VKontakte | — | 07 |
| Search Grid Generator | fácil | Grade KML para busca sistemática de área | — | 08 |
| Shadow Chronolocator | fácil | Data e hora a partir de sombras, com o local conhecido | — | 05/08 |
| OpenAI Whisper | fácil | Transcrição e tradução de áudio e vídeo | ✔ | 02 (texto para extração) |
| Holehe | fácil | Contas associadas a um e-mail | — | 07 |
| Maigret | fácil | Contas associadas a um username | — | 07 |
| Wayback Machine Downloader | fácil | Baixa um site inteiro do arquivo | — | 07 |
| yt-dlp | fácil | Baixa vídeo de centenas de plataformas | — | entrada do Whisper |
| ExifTool | médio | Metadados de arquivos | — | 05/08 |
| Deepface | médio | Comparação e análise facial | ✔ | ⚠️ ver nota de ética |

> ⚠️ **Reconhecimento facial** trata dado biométrico, que é dado pessoal sensível na LGPD (art. 5º, II, e art. 11). O OSINTIA não inclui esse tipo de notebook. Se for usar, faça só com base legal específica e registre no manifesto.

## Modelos de IA com demo ou uso simples no Colab

| Projeto | Tarefa | Licença | Observações | Encaixe |
|---|---|---|---|---|
| [GeoCLIP](https://github.com/VicenteVivan/geo-clip) (NeurIPS 2023) | Top-k coordenadas GPS de uma foto, com probabilidade | ver repositório | `pip install geoclip`; demo oficial no Colab; a probabilidade não vem calibrada | **08** |
| [StreetCLIP](https://huggingface.co/geolocal/streetclip) | País e cidade zero-shot entre candidatos | **CC BY-NC 4.0** | 1,1 mi imagens de rua de 101 países; viés ocidental; sem Índia e China; imagens privadas fora de escopo | 08 (opcional) |
| [PIGEON](https://arxiv.org/abs/2307.05845v1) | Geolocalização estado da arte (artigo) | ver artigo | Referência de método; o modelo completo não é o foco deste levantamento | leitura |
| [qwen_OSINT](https://huggingface.co/aab20abdullah/qwen_OSINT) | LLM ajustado para relatórios de OSINT (GGUF) | Apache-2.0 declarada | Cartão não informa dados de treino nem avaliação e é contraditório sobre o modelo base. Bom **estudo de caso** para o notebook 00 | 00 |
| [OpenAI Whisper](https://github.com/bellingcat/open-source-research-notebooks) (via Bellingcat) | Transcrição multilíngue | MIT | Roda no T4 | 02 |

## Comportamento coordenado

| Projeto | O que faz | Licença | Observações | Encaixe |
|---|---|---|---|---|
| [coordination-network-toolkit](https://pypi.org/project/coordination-network-toolkit) (QUT) | Co-retweet, co-tweet, co-similaridade, co-link, co-reply, co-post em janela de tempo; exporta GraphML | MIT | Aceita CSV genérico; última versão 1.5.2 (2022) | **09** (método reimplementado; comparação opcional) |
| [Phantomatics](https://github.com/jerzy99jerzy/phantomatics) | Funde seis sinais num grafo e detecta comunidades | ver repositório | Atribuição **nunca** automatizada, garantido por teste. Dados de exemplo sintéticos | **09** (princípio adotado) |
| [CooRTweet](https://packages.oit.ncsu.edu/cran/web/packages/CooRTweet/readme/README.html) | Coordenação em R | ver CRAN | Alternativa para quem usa R | 09 |

## Satélite e mudança na paisagem

| Projeto | O que faz | Licença | Observações |
|---|---|---|---|
| [earthchange](https://pypi.org/project/earthchange/) | 29 cenários de mudança (desmatamento, queimada, enchente, urbanização) com Sentinel-1/2 | MIT | Versão 0.2.0 publicada em 11/10/2026, um único mantenedor: espere amadurecer |
| [Change Detection in Earth Engine — MAD](https://developers.google.com/earth-engine/tutorials/community/imad-tutorial-pt1) | Tutorial de detecção de mudança (iMAD) | tutorial oficial | Base metodológica sólida, roda no Colab com conta do Earth Engine |

## Coleções e agentes

- [awesome-colab-notebooks](https://github.com/amrzv/awesome-colab-notebooks): coleção geral de notebooks de IA; útil para achar modelos novos.
- [python-OSINT-notebook](https://awesome.ecosyste.ms/projects/github.com%2Ftegridydev%2Fpython-osint-notebook): guia escrito de técnicas de OSINT com Python.
- [OpenOSINT](https://github.com/OpenOSINT/OpenOSINT): agente de OSINT com REPL, servidor MCP e CLI; funciona com modelos locais.

## O que já entrou no OSINTIA a partir desta lista

| Ideia | Origem | Onde está |
|---|---|---|
| Linha do tempo de IDs de analytics | Bellingcat Wayback Google Analytics | `osintia/coleta.py`, notebook 07 |
| Maigret e Holehe na coleta | Bellingcat (community) | notebook 07 |
| Geolocalização top-k com auditoria em km | GeoCLIP | `osintia/geo.py`, notebook 08 |
| Co-link, co-texto, co-repost em janela | coordination-network-toolkit | `osintia/coordenacao.py`, notebook 09 |
| Atribuição nunca automática | Phantomatics | `coordenacao.resumo_grupo` (testado) |
