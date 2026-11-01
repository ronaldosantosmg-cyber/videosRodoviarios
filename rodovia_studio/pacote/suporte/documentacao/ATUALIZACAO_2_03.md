# Rodovia Studio 2.03 — motor de microssimulação e guarda anti-conflito

**Estado: NÃO validada pelo gate completo (`validar_entrega.py`). Nada foi publicado em `main`.**

## Feito
- `app/microsim/` (novo, autônomo): IDM com folga mínima s0 ≥ 2,0 m e T ≥ 1,2 s, frenagem de emergência por TTC/folga, líderes virtuais
  (semáforo fechado, faixa de pedestres, interdição); MOBIL com critério de segurança e de incentivo, bloqueio estrito por
  canteiro/barreira/bordo/linha contínua, merge em zíper antecipado proporcional à velocidade; seta ≥ 1,0 s antes do movimento
  lateral, mantida na transição, apagada ao centralizar, seta oposta no retorno; transição suave (smoothstep) com rumo tangente;
  OBB + SAT + grelha espacial como fail-safe (congela o veículo de trás).
  Interfaces: `Lane` (eixo + limites), `LayerRules.classify(nome_da_layer)`, `parallel_lanes(...)`, `TrafficSignal`, `StopLine`, `LaneClosure`.
- `app/conflict_guard.py` ligado ao `TrafficSim`: barreira final, depois de todas as barreiras existentes. Só atua se dois corpos
  (com a folga lateral do aplicativo) se sobrepõem; então o veículo de trás volta ao estado do passo anterior e fica parado.
  Antes, o caso interrompia o vídeo com "Reserva lateral insuficiente". Chave: `traffic_conflict_guard` (padrão ligado).
  O relatório da simulação traz `conflict_guard` (intervenções, pares, não resolvidos).

## Medido (neste ambiente Linux)
- `tests/test_microsim.py`: 14 testes passam (IDM, semáforo, seguidor/emergência, ultrapassagem com seta, transição monótona,
  limites das layers, zíper sem entrada na interdição, fail-safe com IDM sabotado, 75 veículos × 3 faixas sem sobreposição).
- `tests/test_v14239_conflict_guard.py`: resultado idêntico (quadro a quadro) com e sem a guarda quando não há conflito; com as outras
  barreiras desligadas à força, a guarda elimina a sobreposição.
- Testes de tráfego existentes: mesmos resultados do código anterior (falhas restantes de test_v127/test_v133 idênticas na base).

## Não verificado
- Windows nativo / WebView2, projetos reais do usuário, carga prolongada.
- O motor `microsim` NÃO substitui o `TrafficSim` (isso mudaria cálculos); só a guarda está ligada. Só faixas no mesmo sentido (sem ultrapassagem pela contramão).

## Congelado
- Roteamento por menor custo (Dijkstra) e demais itens congelados anteriormente.
