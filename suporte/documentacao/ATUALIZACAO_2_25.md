# Atualização 2.25 (não validada pelo gate completo)

## Resumo do tráfego (comando RESUMOTRAFEGO; abre sozinho ao fim de "Gerar tráfego")
- Mostra faixas por tipo (principal, marginal, retorno, dispositivo, acesso), ligações e proibições, trechos de ultrapassagem pela pista contrária, vãos sem pavimento e se há cortes de fluxo.
- Atalhos em um clique: "Ver cortes no mapa" (DIAGNOSTICARVEICULOS), "Corrigir fluxos…" (CORRIGIRFLUXOS) e "Animar fluxos".
- Teste: tests/test_v14251_via_presets.py (contagem do resumo, via node).
