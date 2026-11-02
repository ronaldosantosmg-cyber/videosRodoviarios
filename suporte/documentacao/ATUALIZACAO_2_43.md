# Atualização 2.43 (não validada pelo gate completo)
# 2.43 — textura em tempo real, várias seções por eixo, faixas e pavimento

**1. Textura/representação em tempo real (editor 2D).** Trocar Pista nova/existente/acostamento (flexível ↔ rígido), Montagem (técnico/artístico), Texturas (anteriores), o estilo de representação por pista (hachura, placas...) e os ajustes de grão/tom/remendos/fissuras repinta o desenho na hora, inclusive enquanto o controle ainda está sendo arrastado; antes só mudava ao dar zoom. Concreto aparece claro com juntas no espaçamento configurado; o perfil técnico mostra a cor lisa. Arquivos: `99_aparencia_ao_vivo.js` (novo), `94_texturas_vivas.js`, `68_camadas_graficas.js`. Teste de navegador: `test_v14274_textura_ao_vivo.py`.

**2. Várias seções distintas no mesmo eixo.** Pista simples, pista duplicada, um só sentido do eixo e um só sentido OPOSTO ao eixo, cada uma com início/fim por distância (m), por km ou por coordenadas (com clique no mapa). Uma seção nova sobre outras recorta as anteriores sem erro. A janela ganhou “Sentido do fluxo desta seção” e a lista mostra tipo e sentido de cada seção. Teste de navegador pelas janelas reais: `test_v14273_varias_secoes_no_eixo.py`.

**3. Duas faixas no mesmo sentido.** Com pavimento para as duas faixas, as duas circulam (testado). Quando uma faixa não circula, agora o programa diz por quê: aviso por faixa com km inicial/final e o motivo (“sem hachura de pavimento” ou “barreira, canteiro ou exclusão”), no relatório do cálculo de fluxos e no editor (`section_lane_coverage`). No TH53 real, a faixa externa de uma seção de 2 faixas à direita do EIXO_LESTE tinha só 24% sobre hachura: era cortada em dezenas de trechos. Isso depende da posição/larguras cadastradas na seção.

**4. Veículos sobre área sem pavimento (túnel).** Causa: a seção criada por “Escolher eixo” nascia com “usar a seção como pavimento”, o que autorizava circular onde não há hachura. Agora a seção nova NÃO se autoriza; a autorização é POR SEÇÃO (“Circular nesta seção também onde NÃO há hachura de pavimento”) e vale só dentro do intervalo da seção. Seções antigas sem escolha própria seguem a caixa da rota (compatível). Onde a seção autoriza e não há hachura, o relatório avisa o intervalo. Teste: `test_v14272_cobertura_secoes.py`.

Se o seu projeto já tem uma seção criada antes: abra “Seções tipo…”, desmarque “Seções sem escolha própria: circular também onde não há hachura” (ou edite a seção do túnel) e recalcule os fluxos.

Não coberto: vídeo/3D renderizados; gate completo. Falhas antigas dos testes (3D “projeto mudou durante o processamento”, ESLint do test_v131, alguns testes de interface) são as mesmas da 2.40 (comparado lado a lado).
