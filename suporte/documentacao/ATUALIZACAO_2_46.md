# Atualização 2.46 (não validada pelo gate completo)
# 2.46 — Inteligência de veículo articulado no motor de fluxo

- Novo módulo `articulado.py`: modelo do semirreboque do simulador de demonstração (engate no eixo traseiro, θt' = sin(θ−θt)/Lt). Calcula off-tracking, largura varrida, ângulo de articulação e trechos em que a carreta sai da pista. Confere com a fórmula de regime √(R²−Lt²) nos testes.
- `analyze_motion` ganha o campo informativo `articulado` para carreta/bitrem (não altera a validade das rotas).
- O relatório da simulação ganha `articulated_tracking` por percurso onde circulam carretas.
- Nada muda no desenho dos veículos nem nos seus projetos/DXF. Os ajustes visuais experimentais (veículos, taludes, passarelas) foram descartados nesta versão.
- Inclui tudo da 2.45 (nível de serviço A–F). Não validada pelo gate completo.
