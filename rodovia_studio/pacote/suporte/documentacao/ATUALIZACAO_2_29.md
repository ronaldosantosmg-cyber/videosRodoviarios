# Atualização 2.29 (não validada pelo gate completo)

Sentidos dos eixos unificados (cumulativa sobre a 2.28).

- **Causa do EIXO_OESTE não inverter:** o DXF mudou (OESTE passou a ser um eixo único de 9.167 m; antes eram trechos de 9.329 m e 966 m). As escolhas de sentido ficam presas à "impressão digital" de cada eixo e 8 das 9 salvas não casavam com nenhum eixo atual, então nada tinha efeito e não havia aviso. No DXF novo o OESTE ficava "Automático".
- **Política única de sentido** (`direction_policy.py`): ordem de decisão escrita uma vez: seta desenhada › rota cadastrada › OAE › escolha do eixo › escolha do layer › automático. Inverter no trecho e inverter eixo (km) são modificadores.
- **Painel "Sentidos dos eixos" (comando SENTIDOEIXO):** mostra, para cada eixo, o sentido que vale, de onde ele vem e o que foi sobrescrito; permite definir por layer (vale para todos os eixos do layer e sobrevive à troca do DXF); avisa escolhas antigas sem efeito e pode substituí-las.
- Rotas e seções criadas sobre um eixo passam a herdar também a escolha do layer (`source_axis_layer`).
- O motor registra avisos quando uma escolha é sobrescrita por outra e quando uma escolha salva não casa com nenhum eixo.
- Novo endpoint `GET /api/projects/{id}/direction-report` (somente leitura).
