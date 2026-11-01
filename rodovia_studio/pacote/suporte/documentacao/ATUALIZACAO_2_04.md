# Rodovia Studio 2.04 — estabilidade do tráfego, tipologia do eixo, faixas por eixo, texturas

**Estado: NÃO validada pelo gate completo (`validar_entrega.py`), nem em Windows/WebView2. Nada foi publicado em `main`.**
Cumulativo sobre a 2.03.

## Feito
- **Estabilidade do tráfego** (`traffic_stability`, padrão ligado; desligado = comportamento anterior): perfis estáticos por veículo 70% convencional /
  15% lento (70% da velocidade da via, aceleração ×0,6, não vai à esquerda salvo bloqueio) / 15% rápido (110%); só considera ultrapassar com v < 92% da desejada e líder à frente;
  cooldown de 4–6 s após cada troca; histerese Δa > 0,4 m/s²; janela de brecha (frente ≥ máx(8, s0+1,5·v) e seguidor sem frear além de 1,5 m/s²); retorno só com 35 m livres à frente e atrás;
  merge forçado a partir de 120 m antes de interdição total de faixa (ignora só a exigência de janela "marcada"; 'off' e 'deny' continuam valendo; nunca entra em destino bloqueado; se não houver brecha, para na linha); seta apaga com lateral < 10 cm do centro.
  Relatório: `traffic_stability` (perfis, bloqueios por histerese/janela, merges forçados).
- **Tipologia do eixo** (pista simples/dupla, acesso, retorno, dispositivo) controla ultrapassagem e retorno à faixa; acostamento usável com retorno; pavimento ausente = sem veículos, sem erro; linhas transversais (exceto canteiro) ignoradas; juntas de hachura fechadas; linha de bordo conduz.
- **Faixas por eixo** em *Sentidos das vias e nós*: faixas à esquerda, à direita e acostamentos (m). Direita = sentido do desenho; esquerda = oposto. 0 e 0 = veículos sobre o eixo (como antes). Gera um alinhamento ligado ao eixo (`source=eixo_faixas`) com uma seção típica; seções já cadastradas à mão não são tocadas.
- Painel de Configuração sem painel lateral vazio; chamadas idênticas à referência; texturas sobre hachuras (pavimento novo/existente, OAE nova/existente/alargada, corte vermelho com grama, aterro verde com grama, canteiro em grama).

## Medido (Linux)
- Novos: `test_v14241_estabilidade.py` (5), `test_v14241_faixas_eixo.py` (3), `test_v14240_*`; suíte de tráfego (v1404, v14212, v14230, v14239, microsim, v14240_tipologia) passa; 8 falhas de `test_v112.py` são idênticas na base (ambiente).
- Sem colisões traseiras/laterais nos cenários de 1,2 km; merge forçado ≥ 1 confirmado com faixa única bloqueada.

## Não verificado
- Windows/WebView2, UI dos novos campos em navegador real (só `node --check` e geração do alinhamento validada em Python), projetos reais, carga prolongada, juntas de hachura de dados reais.
- "Terraplenos diversos em grama" ainda não implementado. Duração da manobra permanece 4 s (a especificação cita 2 s).

## Congelado
- Roteamento por menor custo (Dijkstra) e demais itens congelados anteriormente.
