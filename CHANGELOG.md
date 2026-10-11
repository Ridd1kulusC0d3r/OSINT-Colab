# Changelog

## 1.1.0 · 11/10/2026

### Novo
- **Notebook 07 · Coleta em fontes abertas:** variantes de imitação, crt.sh, linha do tempo de IDs de analytics no Wayback Machine, Maigret e Holehe; saída pronta para o notebook 01.
- **Notebook 08 · GeoCLIP auditado:** top-5 coordenadas com calibração medida em quilômetros contra o GPS do EXIF; StreetCLIP opcional; exportação KML.
- **Notebook 09 · Comportamento coordenado:** co-link, co-domínio, co-repost e co-texto em janela de tempo, sem atribuição automática; comparação opcional com o coordination-network-toolkit.
- Módulos stdlib `osintia.coleta`, `osintia.coordenacao` e `osintia.geo`.
- Casos sintéticos: campanha coordenada com armadilha da imprensa (301 mensagens) e geolocalizador superconfiante (240 previsões).
- `docs/COLABS-RELACIONADOS.md`: catálogo de notebooks de OSINT da Bellingcat e da comunidade, com licença e encaixe.
- CLI: `variantes`, `coordenacao`, `analytics`.

### Alterado
- 43 testes (eram 24); o validador executa os notebooks 00 e 09 de ponta a ponta.
- README com fluxo de investigação e arquitetura com a etapa de coleta; manual com os novos notebooks, glossário e correção de rolagem no celular.
- Lançadores de dois cliques rodam também a detecção de coordenação.

## 1.0.0 · 10/10/2026
- Primeira versão: núcleo stdlib (calibração, auditoria de rótulos, roteamento, esquemas, custódia, extração) e notebooks 00 a 06.
