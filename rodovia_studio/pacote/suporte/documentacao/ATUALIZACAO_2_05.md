# Rodovia Studio 2.05 — interpretação de layers, hachuras, eixos e diagnóstico de tráfego

**Estado: NÃO validada pelo gate completo (`validar_entrega.py`), nem em Windows/WebView2. Nada foi publicado em `main`.**
Cumulativa sobre a 2.04. O microsimulador (`app/microsim`) continua fora do fluxo, como combinado.

## Feito
- **Interpretação das layers** (`app/layer_report.py`, GET `/api/projects/{id}/layer-report`, botão com ícone em *Áreas e sinalização*): papel de cada layer, origem (projeto / perfil / nenhuma), confiança, tipos de entidade, alertas (sem papel, geometria incoerente com o papel, papel duplo, layer ausente, eixo/pavimento ausentes), exportação CSV. Somente leitura.
- **Cobertura e conflitos de hachuras** (`app/hatch_coverage.py`, GET `/hatch-coverage`): área por papel, sobreposições com prioridade fixa (canteiro > OAE > acostamento > pavimento novo > existente > talude/água/domínio), juntas estreitas (≤ 1 m), vazios largos (até 6 m), hachuras degeneradas, ausência de pavimento. Somente leitura; o vídeo não muda.
- **Terrapleno em grama**: novo papel `terrain` (hachura/layer *gramado*, *área verde*), textura de grama, não bloqueia o fluxo. Textura continua derivada de papel + subtipo (pavimento novo/existente, flexível/rígido, OAE nova/existente/alargada, corte vermelho com grama, aterro verde com grama, canteiro e terrapleno em grama).
- **Continuidade dos eixos** (`app/axis_validation.py`, GET `/axis-validation`): cobertura sobre o pavimento (amostra a cada 5 m), maior trecho fora (estacas), autointersecção, extremidades livres, lacunas das seções cadastradas.
- **Faixas por eixo**: prévia esquemática (esquerda/direita/acostamentos, setas de sentido) atualizada ao digitar em *Sentidos das vias e nós*.
- **Diagnóstico de paradas** no relatório do tráfego (`stop_diagnostics`): segundos·veículo parados por causa (bloqueio, semáforo, pare e siga, pedestres, líder, fim da via), por rota e amostras com estaca; aparece em *Por que os veículos não aparecem?*. Só contabilidade: não altera a dinâmica.
- **Calibração IDM por classe** (`traffic_calibration`: `{classe:{a,b,T,s0}}`, com limites validados). Vazio = comportamento idêntico ao anterior (testado quadro a quadro).
- **Gate rápido**: `validar_rapido.py`; testes novos registrados em `validar_entrega.py`.
- Botões novos com ícone: Interpretação das layers, Cobertura das hachuras, Continuidade dos eixos.

## Medido (Linux)
- DXF do TH57: 30 layers, 18 com papel, 12 com geometria sem papel (estacas, malha, pontos altos/baixos…); 616 juntas e 91 hachuras degeneradas nas hachuras de pavimento; 8 eixos, 1 com 67% sobre pavimento (trecho de 43,7 m).
- Testes novos: layers (5), cobertura (4), terrapleno (3), eixos (3), estabilidade/diagnóstico/calibração (7), faixas por eixo (3). Lote de regressão de tráfego/UI: 86 passam. Comparação por arquivo com a base (testes que tocam perfis, hachuras, rotas e apresentação): nos 15 arquivos já comparados, as falhas são idênticas às da base (ambiente); a comparação dos demais arquivos não foi concluída.

## Não verificado
- Windows/WebView2; aparência real dos novos diálogos em navegador (só `node --check` e testes de backend); projetos reais além do TH57; carga prolongada.
- A calibração não foi ajustada a contagens reais (não há dados); só o mecanismo existe.
- Rotatórias/interseções: sem alteração (mantido o comportamento existente).

## Congelado
- Microsimulador (`app/microsim`) fora do fluxo; roteamento por menor custo (Dijkstra) e demais itens congelados anteriormente.
