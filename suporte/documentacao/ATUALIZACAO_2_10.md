# Rodovia Studio 2.10

**Estado: NÃO validada pelo gate nem em Windows/WebView2. Mudanças de tráfego/geometria sem teste executado (ambiente de montagem sem shapely/pytest).** Cumulativa sobre a 2.09.

## Fluxo e linhas de contorno falsas
- A “linha de bordo como guia” (`edge_line_guide`) tornava parede de 16 cm qualquer linha longitudinal da layer de bordo, mesmo no meio da pista (contorno de hachura falso, divisão desenhada na layer de bordo), cortando a área permitida e interrompendo o fluxo. Agora só valem como guia as linhas que seguem o contorno do pavimento (≥ 50% do comprimento a até 1,2 m dele). As internas são ignoradas e contadas no relatório (`edge_lines_ignored_inside_pavement`).

## Semáforo
- Amarelo com zona de dilema: quem consegue parar (frenagem ≤ 4,5 m/s²) freia; quem não consegue atravessa. Onda verde passa a exigir o mesmo amarelo nos semáforos ligados.

Demais itens como na 2.09.
