# Levantamento 2.01 — continuidade da 1.42.38

Base local dee654d, branch desenvolvimento/rodovia-studio-1.42. Fetch remoto apontou para ancestral b956ba1 (54 commits atrás), sem commits exclusivos remotos. Nenhum reset, force push ou alteração da main autorizado/realizado.

| Domínio | Implementação mantida | Situação e ação 2.01 |
|---|---|---|
| Persistência | 01_estado_configuracao, project_state, store | Fila, revisão otimista e gravação atômica mantidas; listas CAD ordenadas sem alterar catálogo fonte |
| Vista | 02_vista_imagem_web, 54_vista_3d, 66_contexto_imagem | 3D já retém câmera em reconstrução; corrigidos zoom por resize e reenquadramento na captura 2D |
| Formulários | 59_paineis_destacados, 64_janelas_modelagem | Rascunhos e descarte existentes; Aplicar mantém painel e redefine base; validação antes do callback |
| Atualização | 75_operacao_consolidada, 76_politica_atualizacao | Fila/deduplicação e política mantidas; retirada espera concorrente de 120 s do módulo 64 |
| Acompanhamento | 07_tarefas_intervencoes, 87_circulacao_simples | Correções 1.42.38 mantidas, não reenviar cálculo por falha de GET |
| Tráfego | traffic, routes, road_sections, flow_nodes, oae_traffic, flow_fit | Motor único mantido; contornos decorativos não são obstáculos; orientação de saída de superfície melhorada |
| Materiais | asset_catalog, pavement, 63_catalogo_materiais | Catálogo e mapeamentos mantidos; amostra local de superfícies no 2D, sem iniciar cálculo |
| Cache | 68_camadas_graficas | 2 auxiliares + principal existentes; aparência incluída na chave técnica; fundo independente |
| Menus | 75, 78, 80, 88 e interface/ | Cinco abas existentes reutilizadas, contraste/foco e ícones distintos aprimorados |
| Logs/IA | execlog, usagelog, usage_catalog, assisted_execution | Uso, erro e processamento já separados; ações permitidas e validação mantidas; sem executar código externo |
| Exportação | worker, render, capture3d | Mesmo pipeline; exportação exige revisão válida e testes MP4 reais |
| Compatibilidade | rotas/paginas, 99_registros | app.js é rota dinâmica de compatibilidade, não lixo; wrappers registrados mantidos |

Não há evidência suficiente para apagar módulos legados completos: as chamadas são dinâmicas. A limpeza efetiva remove o mecanismo duplicado de espera no formulário. Nenhuma limpeza de dados de usuário.

Pendências fora desta comprovação: núcleo CAD completo, classificação semântica autônoma da imagem, LLM 3B incorporado, veículo normativo completo de cada categoria, certificação normativa, carga prolongada Windows/8 GB e reprodução do projeto salvo específico do usuário.
