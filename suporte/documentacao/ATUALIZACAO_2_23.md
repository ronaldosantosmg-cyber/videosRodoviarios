# Atualização 2.23 (não validada pelo gate completo)

## Painel "Via" (comando VIA) e "Gerar tráfego" (comando GERARTRAFEGO)
- Tipos de via prontos: pista simples; simples com faixa adicional; duplicada com canteiro; um sentido com eixo no meio; um sentido com eixo no bordo; ramal; rotatória. Miniatura de cada seção, parâmetros (faixas, largura, acostamento, canteiro, sentido, velocidade) e resumo ao vivo das faixas geradas.
- Reaplicar um tipo substitui a via do mesmo eixo (mantém identidade).
- Gerar tráfego: semente (mesma semente = mesma animação) e densidade; salva e recalcula em um passo.
- Backend: app/via_presets.py, rotas /api/via/presets e /api/via/montar, Settings.traffic_seed (entra na invalidação de simulação).
- Testes: tests/test_v14251_via_presets.py (os testes de tela não rodam aqui).
