# Rodovia Studio 2.15

**Estado: NÃO validada pelo gate completo nem em Windows/WebView2.** Cumulativa sobre a 2.14.

## Uma linha por posição (sem duplicidade)
Regra única: **a linha do DXF (contorno externo do hatch de pavimento e camada Bordo) vence a gerada**.
- Contorno do hatch no editor (`webmap.py` + `02_vista_imagem_web.js`): passa a ser só o limite **externo** da união dos hatches de pavimento/existente/acostamento/OAE. Juntas internas entre blocos, sobreposições (pista nova sobre existente) e segmentos coincidentes entre registros não são riscados (o preenchimento não muda).
- Linhas perpendiculares: segmentos de contorno transversais (> 60°) ao eixo mais próximo (até 30 m, comprimento ≤ 40 m — fim de bloco de hatch) não são riscados no editor e não geram linha de bordo na sinalização (`edge_lines` ignora; contador `perp_dropped`).
- Sinalização gerada pela seção (`signage.lane_lines`): bordas brancas a menos de 1,2 m do contorno/Bordo do DXF e tracejados a menos de 0,6 m são removidos (contador `auth_dropped`).

Testes executados (sintéticos): contorno de 3 blocos em série + 1 sobreposto só mantém os bordos externos; nenhuma junta transversal; borda gerada cede ao contorno; segmento perpendicular detectado. NÃO verificado com o seu DXF nem na tela; a linha clara central da 1ª imagem (seção/hatch selecionado) pode exigir o projeto salvo para reproduzir.
