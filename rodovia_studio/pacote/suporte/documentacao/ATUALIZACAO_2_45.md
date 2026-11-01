# Atualização 2.45 (não validada pelo gate completo)
# 2.45 — Nível de serviço A–F

- Novo seletor "Nível de serviço alvo (A–F)" no painel de tráfego: a demanda por faixa é calculada para cair no meio da faixa de v/c do nível escolhido (F = acima da capacidade). "Manual" mantém o comportamento anterior.
- Tabela por tipo de via: pista simples (% de tempo em pelotão + velocidade) ou pista dupla/multifaixa (densidade). Automática pelo número de faixas, ou escolhida.
- O relatório da simulação agora traz `level_of_service`: nível medido (densidade, velocidade, % em pelotão, v/c por faixa).
- ATENÇÃO: limiares são os do HCM 2000 como o DNIT adota, escritos de memória; NÃO conferidos com o seu exemplar do manual. São editáveis em `service_level_table`.
- Novo teste independente de impacto: retângulos reais de todos os veículos, quadro a quadro, sem sobreposição.
- Teste de pare e siga atualizado para o modo adaptativo (padrão desde 1.42.43).
- Conhecido: 3 testes antigos de ponta a ponta (ultrapassagem na simulação real, sonda de acostamento, pedestres no vídeo) já falhavam na 2.44 e continuam; em investigação.
- Não validada pelo gate completo.
