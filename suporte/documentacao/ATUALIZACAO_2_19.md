# Atualização 2.19 (não validada pelo gate completo)

## Pista dupla, eixo e faixas
- Seção tipo (`CrossSection`): `left_dir`/`right_dir` ('mesmo'|'contrario'). Padrão inalterado (dois sentidos).
- Eixo no MEIO da pista: faixas dos dois lados no mesmo sentido; canteiro obrigatoriamente 0 (validação).
- Eixo no BORDO: pista só de um lado (o outro pode ser só acostamento ou vazio); o canteiro fica entre este eixo e o do outro sentido.
- Numeração das faixas: 0 = mais à esquerda da marcha, cresce para a direita (vale para os dois sentidos).
- Larguras por faixa (`section_lane_widths`) e pare e siga só em seção padrão de dois sentidos.
- Rota de sentido único (`axis_ref`: centro | bordo_esquerdo | bordo_direito), em rota e em trecho.
- Percurso decrescente de seção unidirecional: espelha e renumera as faixas.
- Telas: Seções tipo (nova seleção "Posição do eixo e sentido das faixas", 0 faixas permitido), Faixas do eixo (sentido das faixas à esquerda), Propriedades da rota (Posição do eixo).

## Contorno de hachura
- Hachuras de pavimento só têm o contorno traçado onde há linha real do DXF por baixo (tolerância 0,8 m); o preenchimento não muda. Contorno sem nenhuma linha real fica inteiro.
