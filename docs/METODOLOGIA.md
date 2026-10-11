# Metodologia, tradecraft e ética

## Onde a IA entra no ciclo de inteligência

| Fase | O que a IA faz no OSINTIA | O que continua humano |
|---|---|---|
| Planejamento | Nada | Pergunta de inteligência, escopo, base legal |
| Coleta | Notebook 07 gera variantes e consulta crt.sh, Wayback, Maigret e Holehe | Escolha das fontes, base legal, registro da coleta |
| Processamento | GLiNER extrai entidades; e5 e o 09 agrupam contas; visão e GeoCLIP localizam imagens | Conferir extrações, grupos e coordenadas |
| Análise | Modelo de decisão tria; DeepSeek-R1 preenche ACH | Decidir casos abaixo do limiar, julgar hipóteses |
| Disseminação | Mascaramento LGPD; manifesto de custódia | Assinar o relatório e responder por ele |

## Princípios

1. **Modelo não é fonte.** A saída de um modelo é um processamento sobre fontes. No relatório, cite a fonte original, nunca "a IA disse".
2. **Decisão fechada, confiança medida.** Prefira perguntas com opções definidas e probabilidade calibrada a texto livre.
3. **Humano no circuito por padrão.** Todo caso abaixo do limiar vai para o analista (`roteamento.rotear`).
4. **Audite o rótulo antes do modelo.** Veja `AUDITORIA-DE-ROTULOS.md`.
5. **Custódia desde o primeiro arquivo.** Registre coleta, inferência e decisão no manifesto (`custodia.registrar`).
6. **Raciocínio não é evidência.** O texto em `<think>` do DeepSeek-R1 ajuda a entender o modelo; não prova nada.

## Escala do Almirantado no relatório

Combine a confiabilidade da fonte (A–F) com a credibilidade da informação (1–6), por exemplo **B2**. O esquema `confiabilidade_fonte` ajuda na triagem, mas a nota final é do analista. `roteamento.codigo_almirantado("B", 2)` monta o código.

## Ética e LGPD

- **Finalidade legítima.** Use para proteção de marca, resposta a incidentes, pesquisa e investigação autorizada. Não use para perseguir, expor ou assediar pessoas.
- **Minimização.** Colete e guarde só o necessário. `extracao.mascarar` remove CPF, CNPJ, telefone e e-mail de relatórios compartilhados.
- **Pessoas privadas.** Evite construir perfis de indivíduos sem base legal. O caso de demonstração é sobre uma **marca** fictícia e contas que a imitam.
- **Coordenação não é autoria.** O notebook 09 aponta contas que agem juntas; quem está por trás é uma conclusão humana, com evidência independente. Imprensa, campanhas e movimentos sociais também coordenam.
- **Biometria fica de fora.** Reconhecimento facial trata dado biométrico (LGPD, art. 5º, II, e art. 11). O OSINTIA não inclui esse tipo de notebook.
- **Coleta com moderação.** `osintia.coleta` espera 1,5 s entre requisições e se identifica com User-Agent próprio. Respeite os termos de uso de cada serviço.
- **Dados sensíveis.** Saúde, religião, orientação sexual e similares exigem base legal específica (LGPD, art. 11). Não treine modelos com esse tipo de dado sem ela.
- **Transparência.** Registre no relatório quais modelos foram usados, com que versão e com que limiar.

## Limiares sugeridos para começar

| Decisão | Limiar inicial | Motivo |
|---|---|---|
| Arquivar / descartar | 0,90 | Errar aqui some com uma ameaça |
| Monitorar | 0,70 | Erro barato, revisável depois |
| Escalar / bloquear | 0,80 | Erro gera custo para o cliente |

Ajuste com `roteamento.varrer_limiares` sobre o seu conjunto de auditoria.
