# Rodovia Studio 2.14

**Estado: NÃO validada pelo gate completo nem em Windows/WebView2.** Cumulativa sobre a 2.13.

## Correção do mapa que descia (substitui a correção da 2.12)
- A 2.12 reservava espaço fixo para a barra da seleção; ao aparecer, o mapa ainda descia. Agora a barra **não participa do layout**: volta a flutuar sobre o mapa (posição absoluta no quadro do desenho), como no desenho original, e nunca altera a altura da tela. Não verificado no WebView2.

## Ultrapassagem pela pista contrária (pista simples)
- Novo `passing_zones.py` (puro): um trecho só permite ultrapassagem se o raio ≥ 220 m, houver visibilidade de 180 m à frente (desvio da corda ≤ 3 m) e estiver a ≥ 60 m das pontas; seções “proibir” e modo “off” do eixo bloqueiam; se houver seções “permitir”, a manobra tem de caber numa delas.
- `ShoulderProbe.try_pass_oncoming`: um veículo só tenta depois de seguir de perto (2–45 m) um veículo bem mais lento, em sentido igual, com faixa de sentido oposto ao lado (1,5–8 m) e pavimento cobrindo todo o corpo na pista contrária; recusa se houver veículo em sentido oposto dentro da distância que ambos percorrem durante a manobra + 60 m; o retorno exige folga; colisão prevista com qualquer veículo recusa. Canteiro/barreira não são atravessados (cobertura do pavimento).
- Só uma fração dos veículos (padrão 25%, sorteio determinístico) tem perfil de ultrapassador; pesados e perfil “lento” nunca ultrapassam pela contrária. Configuração: `opposite_overtake` (padrão ligado) e `opposite_overtake_share`.
- Editor: trechos permitidos aparecem em verde translúcido (apenas estudo técnico).

Verificado aqui (teste de unidade com cenário sintético): passa e retorna sem sobreposição; recusa com veículo oposto, trecho proibido, modo off, sem faixa contrária, sem pavimento na contrária, desligado ou sem ultrapassadores. NÃO verificado: simulação completa em projeto real, animação no vídeo e desempenho.

## Sinalização fiel ao eixo do DXF
- A linha central amarela dupla (eixo de dois sentidos) estava no MEIO DO PAVIMENTO, e as divisórias de faixa partiam do bordo filtrado do pavimento; por isso não coincidiam com o eixo cadastrado. Agora, para eixo nativo do DXF: a linha central fica exatamente sobre o eixo; e, quando o eixo está junto a um bordo (pistas duplicadas, eixo na borda do canteiro — menos de 0,6 faixa), as divisórias partem exatamente do eixo, na largura de faixa configurada. Eixo centrado no pavimento mantém o comportamento anterior.
- Teste: divisória gerada a 3,5 m do eixo (±5 cm) em cenário sintético. Não verificado com o seu DXF nem no vídeo.
- 11 testes antigos de sinalização (test_v115/test_v118) já falhavam antes desta versão (fixtures sem eixo cadastrado); não foram alterados.
