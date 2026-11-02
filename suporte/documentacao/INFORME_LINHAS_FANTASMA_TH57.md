# Informe: linhas fantasma no TH57 (rotatória e contornos)

Situação relatada: linhas brancas finas aparecem dentro da rotatória e do ramo no editor a cada atualização.

## O que foi medido (ANTEPROJETO TH57.dxf e assets/th57/projeto.dxf)
- Leitura do DXF e vetores simplificados do editor: 480 mil e 77 mil amostras comparadas com o DXF achatado a 5 mm; nenhuma a mais de 0,5 m. A simplificação matemática NÃO cria cordas.
- Bordos e sinalização gerados (41 mil segmentos): sempre a 0,35 m do contorno do pavimento (máx. 0,68 m).
- As linhas brancas do editor são contornos de hachura de PAVIMENTO (cor branca, 1,9 px) que sobravam: fins de bloco e juntas entre blocos. Com "contornos derivados" ligado o editor usa `source_k`, e a ocultação de juntas internas/fins de bloco só era gravada em `k`.

## Correções (3.2)
1. webmap._dedupe_outlines grava a ocultação também em `source_k`.
2. As guias de direção incluem os eixos de ramos e rotatórias (antes só o eixo principal, alcance 30 m).
3. geometry: filtro de cordas longas (≥30 m) em bordo/sinalização/domínio (app/fantasmas.py).
4. signage: divisórias cortadas em saltos de deslocamento; TrafficNetwork.eliminar_discrepancias compara a pintura gerada com o modelo.
Resultado no TH57: 66 segmentos de contorno de pavimento na rotatória → 5.

## Como confirmar que a atualização está valendo
- Depois de instalar, abra o projeto e rode Analisar de novo (vetores e editor são derivados e ficam "desatualizados" até isso).
- Abra `vectors.json` do projeto: deve conter `"ghost": {"versao": "3.2", "segmentos_ocultos": N}`. Sem essa chave, o aplicativo ainda está executando a versão anterior (reinicie o servidor/aplicativo e reanalise).
- Se a linha persistir, envie print com km aproximado e o `vectors.json`: o campo `ghost` e as camadas dirão se é contorno de hachura (pavimento, branco) ou outra classe.

## Limites
- Gate completo (validar_entrega.py) não executado: faltam Mono e WebView2 no ambiente de geração.
- Contornos de hachura sem nenhuma linha real do DXF por baixo e sem junta interna continuam desenhados (não há como distinguir de borda legítima).

## 3.2.1 — causa adicional encontrada no desenho do canvas (editor)
Em `02_vista_imagem_web.js` (buildVectorPaths), contornos de hachura com segmentos ocultos (`source_k`) eram desenhados com `moveTo` a cada reinício e fechados com `closePath()`. Em Canvas/Path2D, `closePath()` liga o ponto atual ao ÚLTIMO `moveTo` (o reinício após o trecho oculto), não ao 1º vértice: surgia uma corda diagonal entre o fim do anel e o ponto de reinício. Agora, quando há trechos ocultos, o fechamento é um `lineTo` explícito ao 1º vértice. Teste: tests/test_v32_canvas_fechamento.py (reproduz a corda no código antigo e prova a ausência no novo). Versão do vectors.json: `ghost.versao = 3.2.1`.
