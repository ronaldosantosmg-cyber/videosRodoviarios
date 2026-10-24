# Rodovia Studio 1.41 — Versão Final para Uso Prático

## Correções finais
- Interface: `lane_change`, `marked`, `safe` e `off` não são apresentados ao usuário; rótulos em português.
- Rotas explícitas com menos de 50 m permanecem apenas para revisão e são automaticamente desabilitadas para veículos. Novas rotas <50 m são recusadas no momento da criação.
- O motor de tráfego não reabilita microtrechos como fallback quando o filtro de 50 m elimina a rota segura.
- Mudança de faixa protege entradas não finitas, distância nula e índice inválido.
- Modelos Pydantic continuam com `allow_inf_nan=False`; matriz final cobre NaN/±Inf, zero e campos inválidos.
- KMZ e cache persistente de GeoTIFF permanecem protegidos.

## Validação executada
- 50 testes técnicos/regressões focados: aprovados.
- 25 testes visuais Chromium (1.40.7–1.41): aprovados.
- 9 testes de robustez/tráfego 1.40.5: aprovados.
- Python compileall: aprovado.
- JavaScript `node --check`: aprovado.
- O workflow histórico completo é muito pesado para o limite desta sessão e não foi contado como aprovado nesta rodada; os workflows focados e regressões recentes foram executados.

## Instalação
Use `INSTALAR_ATUALIZACAO.cmd` na raiz da entrega. O atualizador cria snapshot/rollback antes de substituir arquivos.
