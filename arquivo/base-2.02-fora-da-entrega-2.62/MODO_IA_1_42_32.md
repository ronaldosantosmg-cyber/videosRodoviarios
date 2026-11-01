# Modo IA — estado auditado na revisão 1.42.32

Esta revisão corrige a confirmação das edições da interface. O levantamento abaixo descreve o código existente; não representa a entrega de um novo modelo de IA.

| Recurso | Estado confirmado | Limite / pendência |
|---|---|---|
| Diagnóstico local de logs | Regras agrupam erros, versões, evidências, hipóteses e passos de correção. Também há estatísticas de duração e recomendações de desempenho. | Não determina uma causa não registrada. Lê registros retidos do projeto, não todos os logs de todos os programas. Não aprende nem altera o próprio código. |
| Layers, texturas e eixos | Modos normal, regras locais e manual; revisão de correlações; aplicar textura/eixo; perfis com salvar, salvar como, importar e exportar. | Atribuir uma camada como eixo não resolve sozinho origem, sentido, seção, nós ou geometria. Não é reconhecimento semântico universal. |
| Correção assistida de fluxos | Ações cadastradas recover/reconstruct, prévia isolada, validação pelo motor real, conferência de revisão/fontes, aplicação confirmada e desfazer. | Não reconstrói qualquer rede defeituosa nem libera barreiras para eliminar avisos. Algumas situações exigem editar o projeto. |
| Prompt para outra IA / importar resposta | Exporta contexto e contrato JSON; a resposta é validada, revisada e limitada a tipos/materiais/ações permitidos. | Uma resposta textual não se transforma em programa executável ou alteração arbitrária de configuração. |
| API online | Adaptador e janela para OpenAI, Groq e OpenRouter; chave em memória da sessão, mini prompt revisável, consentimento por consulta, contrato de resposta e cancelamento. | Requer configuração e chave válidas. Testes de transporte usam provedores simulados; falta homologação com serviço real. Não foi feito treinamento específico do modelo no Rodovia Studio. |
| Modelo local 3B | Adaptador sob demanda, manifesto com hashes, perfil CPU com contexto 2048, uma consulta por vez, saída limitada e descarregamento. | Os pesos GGUF e o runtime portátil não integram o pacote entregue. Candidato indicado no código: SmolLM3-3B Q4_K_M, sem inferência homologada. Não há ensaio real de qualidade/latência/memória em Windows de 8 GB. |
| IA em todas as fases | Há mini prompts para arquivos, fluxo, estaqueamento, texturas, vídeo e diagnóstico geral. | Nem toda fase tem executor automático. Em arquivos, vídeo e estaqueamento, a resposta normalmente orienta e abre a ferramenta correspondente. A aplicação automática exige executor cadastrado e validado. |

## O que os registros de uso fazem

O diagnóstico consulta até 3.000 eventos de execução e 1.000 registros de erro retidos, além de trechos de error.log e ffmpeg.log quando existem. Agrupa até os 100 problemas finais e sugere caminhos de tratamento. Esses limites são de processamento e não apagam os originais por causa desta consulta. Logs rotacionados/ausentes e informação não registrada não são reconstruídos por inferência.

O catálogo de uso calcula amostras, média, p95 e máximo das durações disponíveis. Isso não equivale a treinamento, prova de causalidade ou correção autônoma de qualquer falha.

## Pendências históricas principais ainda confirmadas

1. Entregar e avaliar o pacote local 3B completo em dados representativos e no PC de 8 GB; medir qualidade, RAM, latência e cancelamento, sem concorrência com renderização.
2. Homologar a API online real. Preservar o contrato JSON e a separação entre sugestão, validação e aplicação; não transformar texto externo em comandos livres.
3. Ampliar os executores assistidos por fase, principalmente ajustes de vídeo/estaqueamento/arquivos, com prévia, verificação, snapshot e desfazer. Hoje não há um executor universal.
4. Reconhecimento semântico autônomo de imagens: há análise assistida e adaptador ONNX com exigência de pesos/avaliação identificados; não há um modelo completo homologado entregue para todas as classes solicitadas.
5. Correção integral de qualquer rede: os nós e o motor existente cobrem casos validados, mas não inventam ligações impossíveis, rampas entre níveis ou solução normativa universal. O projeto salvo com fluxos vermelhos/amarelos precisa de reprodução específica.
6. Núcleo CAD completo: já há arcos analíticos e avaliação de NURBS; continuam faltando a amplitude de operações e o kernel de um CAD profissional completo. O WebGL existente não equivale à apresentação do Twinmotion.
7. Dinâmica articulada de composições longas: o envelope rígido conservador de 30 m não é um veículo articulado homologado.
8. Validação prolongada Windows/WebView2 e PC de 8 GB, calibração de tráfego por empreendimento e acompanhamento de desempenho. Testes Linux/Chromium/Mono não substituem essa etapa.

## Proteção dos dados

Já existem revisão da configuração, histórico, integridade, recuperação de cópia conferida, snapshot, fechamento controlado e rollback. A assistência recusa propostas de outro projeto ou obsoletas. Isso não permite recuperar um DXF, KMZ, imagem ou vídeo original ausente quando não existe uma cópia válida.

## Onde verificar no código

- assistance.py e usage_catalog.py: diagnóstico, correlações e métricas de registros retidos.
- assisted_execution.py: executores de fluxo permitidos e conferência antes de aplicar.
- small_ai.py e js/83_ia_pequena.js: adaptador local/online, contrato e encaminhamento para ferramentas.
- js/77_assistencia_ia.js: interface de diagnóstico, perfis e revisão de respostas.
- image_semantic.py: contrato de pesos e avaliação do modelo semântico.
- cad_curves.py: recursos geométricos já presentes e seus limites.
- project_integrity.py e project_state.py: proteção e recuperação da configuração/fontes.
