# Auditoria de comandos, botões, menus, abas e dados — Rodovia Studio 1.42.36

Base: commit `14973929b2695f43369de39608f644f790929196`, branch `desenvolvimento/rodovia-studio-1.42`. Auditoria solicitada pelo usuário; sem mudanças no produto, motor, versão ou pacote. Main não foi alterada.

## Conclusão

A principal duplicidade é de operação e edição: o aplicativo oferece várias portas para a mesma configuração, misturadas com ferramentas antigas que gravam representações diferentes de uma intenção semelhante. Não há evidência de que todos esses botões executem motores independentes. A maior oportunidade é consolidar os editores de tráfego, materiais e assistência, mantendo ícones e atalhos que chamem os mesmos comandos.

Prioridade: uma central de tráfego que preserve nós, sentido e reversão; uma seção típica como editor principal; uma central de materiais; uma assistência contextual; um contrato de confirmação; um registro de comandos usado por menu, ribbon, contexto, favoritos e teclado.

## Método e alcance

- Leitura do HTML, dos módulos JS carregados e dos caminhos de configuração/API relevantes. Navegação real no Chromium com projeto sintético isolado; abertura dos oito menus e seus submenus, alternância das cinco abas. Nenhuma exclusão ou alteração no projeto do usuário.
- Inventário inicial: **404 elementos HTML** entre controles, botões, títulos e summaries; **454 instâncias de botão/summary** e **329 campos** após inicialização. Esses universos se sobrepõem: não somar. Incluem elementos ocultos e infraestrutura; não equivalem a 454 funções.
- Foram registradas **656 linhas de referências JS** de eventos, comandos e extensões, **78 entradas/aliases no COMANDOS**, **21 ferramentas estendidas em FERRAMENTAS**, dentro das **63 ferramentas-base em TOOLS** (63 IDs distintos, não 84). Foram percorridas **165 entradas/cabeçalhos de menus e submenus**. O registro COMANDOS não é o conjunto completo de comandos interpretados: há despacho CAD e ferramentas-base.
- Inventário registra as condições da sessão. Popups criados sob demanda e listas de objetos variam com o projeto; a leitura de suas implementações complementa a navegação, mas não equivale a executar todas as ações.
- Nenhum ID de campo repetido no DOM carregado e nenhum erro JS de página nessa navegação. Há campos e formulários diferentes para os mesmos atributos, o que é outro tipo de duplicidade. Isso não constitui regressão funcional completa, teste de todos os diálogos, desempenho Windows ou validação do motor. Não houve exportação de vídeo nesta auditoria de interface.
- “80% de igualdade” é **triagem funcional**, não porcentagem de código: comparar objeto-alvo, intenção, dados alterados, resultado e caminho de execução/validação. Quatro dimensões próximas em cinco indicam forte candidato a consolidação. Uma diferença de escopo, segurança ou persistência pode impedir a fusão mesmo nessa faixa.
- Classificações: **atalho idêntico** (mesma implementação), **alta sobreposição** (objetivo próximo, implementação/escopo diferentes), **parcial** (família comum com resultados distintos), **complementar** (preservar separado). Não inferir código morto por quantidade de acessos.

## 1. Duplicidades prioritárias

| Grupo | Pontos encontrados | Classificação | Dados/execução e decisão |
|---|---|---|---|
| 1. Escolher eixo / configurar faixas | Botões Escolher eixo, Configurar faixas; menu Escolher eixo e configurar faixas; ícone Seção típica; comando SECOESTIPO/PARESIGA; propriedades do alinhamento | Alta; alguns atalhos idênticos | `RodoviaSections.chooseAxis/open` no módulo 65. Sem alinhamento selecionado, Configurar faixas volta ao seletor. Manter dois passos do mesmo assistente e um ícone contextual; não manter seletores concorrentes. |
| 2. Sentidos e extremos | Sentidos e nós (87), Regras dos fluxos → Eixos/nós/giro (85), Nó de entrada/saída/fim (86) | Alta para os campos compartilhados | Todos editam `route_alignments.flow_direction/flow_start/flow_end`. Manter Sentidos e nós como editor; Regras deve mostrar resumo e Abrir editor. Nó na tela é atalho contextual legítimo. Classificação/giro/demanda externa de 85 precisam continuar acessíveis. |
| 3. Criar conexão | Inserir nó de ligação (86), Criar ligação de ramal no menu, Forçar ligação (25), menu de contexto | Alta, não idêntica | Gravam `connection_rules`, mas 86 projeta em trajetória, vincula `from_key/to_key` e oferece parcela/confirmar; 25 guarda dois pontos. Menu Criar ligação de ramal ainda chama `linkforce`. Consolidar no cadastro de nó com vínculo estável; importar regras existentes sem descartá-las. |
| 4. Editar percentuais/ativação da conexão | Editar nó (86), Regras dos fluxos → Conexões e parcelas (85), propriedades de ligações (25) | Alta | Compartilham `connection_rules.share_pct/enabled/action`. Um formulário reutilizável, acessível por tabela ou seleção. Uma janela aberta mantém cópia de regras; impedir sobrescrita de edições mais novas mediante revisão. Risco de arquitetura, não travamento reproduzido nesta auditoria. |
| 5. Correção do fluxo | Corrigir problemas (70), IA assistida (79), Recuperar fluxo principal nas propriedades (61), marca amarela (82), orientação nas propriedades (67), Orientação dos cálculos (71) | Alta na orientação/localização; parcial na execução | Compartilham diagnóstico técnico e `flow_recoveries`, mas 79 oferece proposta, prévia, confirmação e revalidação; 70 executa pedido de reconstrução/análise; 61 recupera partes sem unir lacunas. Uma central com Localizar, Propor correção, Editar; recuperação/recorte/junção avançados. Preservar distinção recuperar/reconstruir. |
| 6. Diagnóstico de veículos | Botão em Tráfego, botão em Vídeo, menu Tráfego, comando DIAGNOSTICARVEICULOS | Atalhos idênticos | Todos chamam `RodoviaTrafficHelp.open` (84), consulta `traffic_status`. Manter atalho em Vídeo e entrada principal em Tráfego; não há motor duplicado nesse caso. |
| 7. Classificar layers e materiais | Configuração → Camadas; Gerenciador de camadas (34); Materiais/símbolos/nomes CAD (63); Analisar layers/IA (77) | Alta na classificação; parcial na visibilidade | Classificações em `cfg.layers`, materiais em `layer_materials`; mesma família de perfis. Uma tabela de classificação com modos normal/regras/manual; manter visibilidade/congelamento como outra função. |
| 8. Perfis de correlação | Catálogo → Salvar perfil/aplicar (63); IA → Perfis reutilizáveis (77); seletor de perfil em Camadas | Alta, duplicidade de fluxo real | 63 usa `/api/layer_profiles`; 77 usa `/api/assistencia/perfis`, ambos apoiados em `layer_profiles.py`, mesmo arquivo `_perfis_camadas.json`. 77 adiciona compatibilidade, revisão/digest e conflito de padrões. Centralizar serviço e editor, mantendo biblioteca. Não há duas bases totalmente independentes. |
| 9. Materiais e texturas | Materiais e texturas (75), seção Materiais e apresentação, Textura nas propriedades, Catálogo (63), Pincel (35), perfil natural (74), aparência do Vídeo | Alta para aparência global; parcial para edição individual | Hub 75 **move controles existentes** para a seção; não clona todos os valores. Catálogo escolhe classes/padrões; textura individual e pincel alteram áreas. Unificar navegação, preservar herança global → camada → área e indicar a origem do material. |
| 10. Salvar / Novo / Abrir | Arquivo; Projeto → Projeto; hub de arquivos; diálogo de projetos; teclado | Vários atalhos idênticos | Menus usam IDs/click dos controles existentes. Redundância visual entre menus Arquivo e Projeto; manter ações de arquivo em Arquivo, ícones rápidos opcionais em favoritos. Não retirar Salvar de toda a interface. |
| 11. Transformações e histórico | Editar → Mover/Girar/etc.; Editar → Propriedades → Modificar; ribbon Editar; contexto; comandos | Atalhos idênticos | `runCommand`, undo/redo e `setTool` compartilhados. O mesmo menu Editar repete comandos dentro de uma segunda hierarquia. Remover a segunda exposição, preservar contexto e teclado. |
| 12. Gerar e visualizar / Atualizar / calcular fluxos | Rodapé Atualizar; Tráfego Gerar e visualizar; Editar → Calcular e atualizar fluxos; comandos de análise | Alta de intenção, execução não idêntica | `RodoviaUpdates`/política 76 atualiza por contexto 2D/3D; análise calcula editor; prévia produz imagem. Um Atualizar central com escopo necessário e opção avançada. Não substituir todos por reconstrução integral. |
| 13. Vídeos e registros | Arquivo → Vídeos gerados; Vídeo → Resultados; Mais ferramentas; logs/suporte/IA | Atalhos idênticos ou escopos complementares | `openVideos` e `openLogs` reutilizados. Logs de execução, último erro e orientação são apresentações do registro, não cópias obrigatórias. Usar Resultados e Diagnóstico como locais principais. |
| 14. Ajuda IA | Logs e melhorias (77), Orientação dos cálculos (71), assistente do fluxo (67), execução (79), mini prompts/API/3B (83) | Alta na experiência; complementar nas capacidades | Unificar janela Assistência com contexto. Regras locais, proposta executável tipada e consulta a modelo são serviços distintos. Adaptador 3B não prova modelo instalado/homologado; consulta online requer consentimento. Não transformar resposta de IA em código executável. |

## 2. O que não deve ser fundido como se fosse igual

| Funções parecidas | Diferença que precisa permanecer |
|---|---|
| Sentidos e nós × Inverter fluxo × Sentido × Girar seta | 87 define via/extremos; `flowrev` grava override no trecho calculado; `dir` insere referência direcional; `arrowrot` gira seta. Não são quatro botões equivalentes. Mostrar alcance e precedência; oferecer reversão da via como principal e override local em avançado. |
| Apagar nó × Desativar regra × Sem conexão | Apagar ligação vira proibição persistente (`deny`) para não reaparecer automaticamente; desativar regra pode voltar ao automático; zona sem conexão atua num raio/polígono. Manter operações distintas e nomes explícitos. |
| Desativar fluxo × Recortar × Apagar eixo | Primeiro mantém geometria e desliga circulação; segundo exclui intervalo; último altera fonte/editável. Nunca promover exclusão geométrica como substituto de desligamento. |
| Juntar subsegmentos × Inserir nó | 62 cria alinhamento unido validado e desliga originais; 86 define movimento entre itinerários e sua parcela. Preservar separado, no mesmo grupo Conexões. |
| Recuperar × Reconstruir | Recuperar conserva partes válidas, podendo deixar lacunas; reconstruir tenta continuidade revalidada. Não prometer conexão onde o motor recusou segurança. |
| Seção tipo × 3ª faixa / Faixas por trecho / Trecho da rota | Mesma intenção de definir faixas, mas gravam `cross_sections`, `lane_ranges`/marcações e `sections` da rota. Migrar e definir precedência antes de esconder editores antigos; não apagar contratos legados. |
| Densidade × demanda horária × VDM × capacidade | Multiplicador de população, veículos/h/faixa, veículos/dia e referência de capacidade não são o mesmo dado. Um seletor de modo com campos condicionais; capacidade separada. Preservar a regra atual de editar densidade/demanda encerrar VDM. |
| Modo clássico × somente simular rotas × simulação protegida | Clássico é ensaio ilustrativo com proteções reduzidas; rota-only restringe população/mudança de faixa; protegido mantém controles físicos. Não criar uma caixa genérica “Liberar tudo”. |
| Testar circulação × Diagnosticar veículos × Inspecionar arrasto | 87 simula amostra curta e audita classes; 84 consulta geração/visibilidade e pode ativar câmera/veículos; 86 mostra envelope técnico do corpo. Reunir como etapas do diagnóstico, não trocar uma pela outra. |
| Regenerar tela × Atualizar × Reconstruir integralmente × Reconstruir 3D | `regenScreen` limpa tiles/vetores/snap; atualização reutiliza derivações; rebuild força reprocessamento; 3D tem recursos próprios. Renomear e separar níveis. |
| Pan/zoom 2D × navegação 3D | Mesmo objetivo perceptivo, motores/câmeras diferentes; permitir mesma linguagem de interface, mantendo implementações próprias. |
| Imagem local comum × georreferenciada × web | Fontes, transformação, licença e cache diferentes. Uma central de imagens deve preservar prioridade, alinhamento e indicação de fonte; não converter tudo para uma imagem reduzida. |
| OAE Z=0 × barreira × ponte com cota relativa confirmada | Z=0 não deve bloquear/reverter por anotação da OAE; canteiro/barreira reais permanecem; desnível confirmado afeta cruzamentos. Classificação física não é apenas material. |
| Hachura técnica × material natural × máscara de exclusão × canteiro | Desenho, apresentação, visibilidade e impedimento físico são domínios diferentes. Não criar barreiras a partir de todos os contornos nem retirar todas as proteções ao esconder hachuras. |
| Prévia 2D × vista 3D × MP4 final | Saídas/caches distintos; compartilham configuração, não validação integral nem identidade visual garantida. |
| Proteção de dados × Histórico × Limpar resíduos × Atualizar aplicativo | Verificar/restaurar configuração, navegar versões, limpar derivados e instalar programa têm alvos e riscos diferentes. Agrupar Manutenção sem transformar em uma única limpeza genérica. |

## 3. Menus superiores, um por um

| Menu | Avaliação atual e decisão |
|---|---|
| Arquivo | Local correto para Novo/Abrir/Salvar/Salvar como/modelos/importação. Sobrepõe grupo Projeto do menu Projeto. Manutenção/atualização/logs misturam finalidades: mover para Ajuda/Manutenção, manter atalhos contextualizados. Histórico e proteção são complementares e devem se chamar reciprocamente. |
| Editar | Repete Mover, Girar, Copiar, Escala, Espelhar/Paralela, Apagar e Desfazer/Refazer dentro de Propriedades. “Outras ferramentas” recebe automaticamente ferramentas não classificadas: inclui nós, recortar fluxo e arrasto; tecnicamente chamadas válidas, localização inadequada. Classificar explicitamente. |
| Projeto | Repetição de operações de arquivo e mistura de configuração, leitura, classificação de layers, alinhamento e rota de veículos. Manter identidade, fontes, CRS, estaqueamento e cadastro de eixo; mandar regras de tráfego à aba correspondente. |
| Tráfego | Maior fragmentação. Quatro ou mais entradas de ajuda/correção, dois caminhos para conexão, seção típica e regras em janelas diferentes. Manter Eixos e sentidos, Seções, Nós, Simular/testar e Diagnóstico; avançados agrupados. **Sentidos e nós e Testar circulação são botões da faixa mas não constam como entradas próprias no menu superior atual**; o menu tem caminhos antigos. Gerar ambos a partir do registro comum. |
| Cena | Coerente como família, mas mistura superfícies físicas, exclusões visuais, estruturas, sinalização e materiais. Não dar mesmo tratamento a canteiro e exclusão decorativa. Catálogo e material individual devem abrir o mesmo contexto com alvos distintos. |
| Vídeo | Mantém produção, câmera e resultados; sobrepõe faixa e hub lateral de Vídeo, o que é aceitável se todos delegarem. “Prévia no instante” e “Gerar prévia” precisam indicar claramente instante, enquadramento e diferença para prévia 3D. |
| Exibir | Vários atalhos legítimos a hubs, navegação e vista3D. A palavra Regenerar deve explicar que limpa apresentação/cache, sem sugerir correção do modelo de tráfego. |
| Ajuda | Local adequado para Assistência, logs, documentação e Sobre. Hoje “IA online”, “Diagnóstico dos logs” e assistência de fluxo parecem serviços sem relação. Oferecer um Assistente com a etapa atual e provedores opcionais. |

## 4. Abas superiores e ferramentas internas

No cenário navegado foram contados os seguintes botões com caixas de layout no painel da aba, incluindo ferramentas expandidas/controles do painel. Não são contagens universais nem todos comandos únicos.

| Aba | Contagem | Diagnóstico |
|---|---:|---|
| Projeto | 13 | Camadas/imagens, API/IA, proteção e controles técnicos. **Corrigir fluxos e Orientação dos cálculos aparecem em Parâmetros de apresentação**, localização herdada sem relação clara com a tarefa. Pair/alinhamento/cabine no grupo herdado Calibração e cabine: cabine pertence a Vídeo/câmera. |
| Editar | 26 | Transformações convivem com cálculo de fluxos, início/fim km, OAE, obra PER e pórtico. Separar editar geometria de cadastrar estruturas e calcular. |
| Tráfego | 43 | Nós indispensáveis, mas muitos modos sobrepostos. Manter ícones de nós em grupo compacto, sentido e seção visíveis; recuperação/forçar/proibições e diagnósticos em expansões coerentes. “Mais ferramentas” e “Mais opções” coexistem: uma única expansão por grupo. |
| Cena | 28 | Materiais + áreas/sinalização + vegetação + navegação3D. Os controles3D de execução, luz, diagnóstico, captura e exportação precisam aparecer apenas em contexto3D; não retirar suas funções. |
| Vídeo | 8 | Faixa mais simples; Diagnosticar veículos é atalho útil para o problema de vídeo vazio, mas deve entrar no mesmo diagnóstico central. Resultado do vídeo e Mais ferramentas organizam ações complementares. |

Inventário nominal coletado das ferramentas e botões em `inventario-botoes.csv`, `inventario-ferramentas.csv` e `interface-executada.json`. A proposta é diminuir escolhas concorrentes, não eliminar acesso rápido: ícones, hover/foco e favoritos continuam.

## 5. Painéis, abas internas e subabas

| Painel/subaba | Duplicidade, dados e recomendação |
|---|---|
| Projeto e arquivos | Campos de identificação compartilhados com Novo projeto e configuração. Novo inicializa; editar altera projeto existente. Um componente de identidade reutilizável, sem pedir confirmação em cada campo. |
| Configuração | CRS, escala, imagem web, hachuras, camadas e sentidos. Muito amplo. Identidade/CRS em Projeto, classificação em Camadas, circulação em Tráfego. Campos devem conservar seus IDs/contratos durante migração. |
| Configuração → Fonte da imagem web | Complementa fonte local e alinhamento; hoje configuração espalhada. Um Imagens com local/georreferenciada/web, prioridade e amostra. Não duplicar o upload. |
| Configuração → Hachuras do DXF | Define `hatch_roles`; pode competir com classe da layer e material individual. Exibir “origem: entidade/camada/padrão”, classe física separada de textura. |
| Configuração → Camadas e sentidos → Cores por tipo | Classificação, cores e autorização circulatória na mesma seção. Separar visibilidade/cor da classificação e do sentido, sem duplicar estado. |
| Camadas, imagem local e intercâmbio | Componente principal de arquivos/imagens e camadas adicionais; repete classificação e links de exportação de Arquivo. Manter central de fontes; menu só encaminha. |
| Camadas → Imagem georreferenciada local | Importação/conversão persistente distinta da imagem comum. Deve mostrar arquivo ativo, cache e georreferência, não virar um segundo seletor desconectado. |
| Camadas → Elevação MDT | Dado distinto da ortofoto e da cota relativa OAE. Manter separado. |
| Camadas → Exportar/importar | Atalho legítimo para intercâmbio. Clarificar pacote de projeto versus perfil de camadas versus resposta IA; não usar o mesmo “Importar” sem tipo. |
| Gerenciador de camadas | Seleção em lote/visibilidade/cor/classe; parte repete tabela da configuração. Um catálogo de camadas com filtros e modos de exibição; não esconder camada da simulação porque foi ocultada visualmente. |
| Propriedades / Modificar / grupos dinâmicos | Devem ser a mesma edição contextual. Hoje 33 agrupa propriedades; 44/59 interceptam abertura; 61/62/67/65/86 acrescentam partes. Melhor registrar extensões por tipo, com um rascunho e uma confirmação. Não excluir módulos só por nome antigo. |
| Marcações do projeto | Geometrias, interdições, áreas e referências. Essas listas são CRUD dos mesmos objetos do desenho, atalhos legítimos; usar mesmo editor individual para tabela e canvas. |
| Ajuste DXF × imagem | Coordenadas/pares e transformação, não o mesmo que mover veículo ou inverter eixo. Preservar cálculo e descarte de resultado obsoleto. |
| Conexões de tráfego (fluxos desenhados) | Regras sobre conexões também acessíveis em nós/propriedades/Regras. Incorporar tabela ao painel Nós, mesmo formulário de edição. |
| Obras PER e cronograma | Tempos/eventos e estruturas; diferente de interdição operacional. Fazer associação explícita, não inferir bloqueio total de qualquer obra. |
| Intervenções e identificações → passarelas/baias | Dimensões e apresentação contextual. Mesmo elemento pode ser criado por botão técnico e editado aqui; isso não é duplicação de cálculo. |
| Exportar vídeo → Exportação | Largura/resolução, fps, duração, qualidade. Separar qualidade do arquivo e resolução do mosaico/imagem de origem. Não oferecer segundo valor de duração na prévia. |
| Exportar vídeo → Câmera | Enquadramento, cabine, pontos e clima/ambiente ainda em agrupamento legado. Mesmos dados acessíveis no painel Vista. Uma câmera persistente com atalhos; navegação temporária não deve sobrescrever exportação sem intenção. |
| Exportar vídeo → Veículos e fluxo | Densidade, demanda e velocidade são configuração de simulação, reutilizada no vídeo. Exibir resumo e link Configurar tráfego; não exigir outro preenchimento independente para exportar. |
| Exportar vídeo → Aparência | Água, luz, sinalização e materiais; sobrepõe Cena. Vídeo escolhe perfil e mostra resumo; ajustes detalhados abrem editor compartilhado de Cena. |
| Exportar vídeo → Avançado | Encoder, workers, mosaico e comparação. Manter recolhido. Ficha técnica/dupla palavra “comparação e comparação” é resíduo de texto comprovado, não nova funcionalidade. |
| Exportar vídeo → Perfil de apresentação, veículos e sentido | Mistura três domínios; mover frota/sentido ao tráfego e manter perfil visual na Cena. |
| Vista, prévia e sessões → Camadas | Exibição transitória de vetores/fundo e vistas salvas; não equivaler à classificação física ou desligamento da circulação. |
| Materiais e apresentação | Reúne controles movidos do formulário principal. Isso reduz duplicação de dados mas ainda mantém vários caminhos de edição. Um local principal com amostra e herança explícita. |
| Assistência → Logs e melhorias | Eventos e orientação; mesma base consultada por guias de cálculo, com agregação diferente. Uma lista unificada com contexto da operação e filtro. |
| Assistência → Layers, texturas e eixos → Perfis reutilizáveis | Editor completo de correlação revisável; sobrepõe catálogo63 e perfis antigos. Melhor candidato a componente principal, aproveitando revisão/hash/compatibilidade. |
| Assistência → Tarefas difíceis/outra IA | Exporta mini contrato e importa JSON; complementar à consulta83, pode ser uma opção “Consultar fora do aplicativo”. |
| IA pequena → geral/arquivos/fluxo/estaqueamento/texturas/vídeo | Escolhas de contexto do mesmo assistente. Não precisam de seis novas abas globais. Resposta encaminha aos editores atuais, sem criar outro motor. |
| Seção tipo → montagem rápida/elementos esquerda-direita/seções/pare-siga | Montagem rápida é um construtor dos elementos detalhados, não outra seção. Mostrar dois modos do mesmo rascunho. Pare-siga usa intervalos e bloqueios relacionados, preservar sua lógica de liberação. |
| Regras dos fluxos → controles/frota/demanda/eixos/conexões/OAE/corredor/desconectados | Janela agrega demais tarefas. Converter em resumo operacional e atalhos dos editores principais; manter controles de segurança e modo de ensaio explícitos. |
| Sentidos e nós → fontes CAD/KMZ/alinhamentos | Dois domínios reais: `route_directions['axis:'+fingerprint]` e propriedades da rota. Já impede controle nativo concorrente de eixo associado à seção. Preservar essa proteção na consolidação. |
| Nós → ligação/extremidade | Ligação usa `connection_rules`, extremidade usa `flow_start/end`; mesmo símbolo não significa mesmo dado. Formulário adapta campos ao tipo. |
| Diagnóstico → arrasto/teste curto/visibilidade | Três níveis complementares: envelope, circulação da frota e câmera. Usar uma central com resultados reutilizáveis e causas localizáveis; não repetir simulação a cada aba. |
| Manutenção, histórico, recuperação e atualização | Dados e programa têm ciclos diferentes. Uma navegação comum, ações claramente distintas, preservação e rollback mantidos. |

## 6. Dados compartilhados e paralelos

| Intenção | Representações atuais | Problema e regra de consolidação |
|---|---|---|
| Geometria de circulação | Fonte CAD/KMZ; `custom_axis`; `route_alignments`; faixas/itinerários calculados | Não são duplicatas removíveis: fonte, cadastro, derivação. Exibir vínculo e responsável por gerar fluxo. Nenhum resultado deve virar eixo autorizado silenciosamente. |
| Faixas/larguras | defaults globais; `route_alignments.lanes/lane_width_m`; `sections`; `cross_sections`; marcações por trecho | Paralelismo de configuração real. Criar resolução central de precedência e mostrar valor efetivo; conversão explícita dos legados antes de desativar editores. |
| Sentido | `reverse_axis`, direções por fonte, `flow_direction`, extremos, marcas/setas e overrides locais | `reverse_axis`/estaqueamento não é sinônimo de reversão de circulação. Mostrar origem da decisão e conflitos, preservar revisão de chave estável da36. |
| Ligação | Conexão calculada, `connection_rules`, zonas sem conexão, papel/extremos do alinhamento | Um nó calculado não equivale a regra cadastrada. UI deve indicar automático, explícito, proibido e desativado. |
| Exclusão/correção | `flow_overrides`, `flow_cuts`, `flow_recoveries`, desligamento de alinhamento/faixa, limite mínimo | Camadas de decisão diferentes podem excluir o mesmo itinerário. Mostrar cadeia de causas por fonte/trecho; uma ação não pode reativar desligamento feito em outra. |
| Demanda | densidade, demanda por faixa, VDM/fração/parcela direcional, entradas externas, percentuais de ramal | Não somar modelos concorrentes sem regra. Modo ativo explícito; entradas externas somam; percentuais redistribuem, não criam veículos. |
| Material | papel físico de layer/hatch; `layer_materials`; materiais globais; áreas e texturas individuais; estilo natural | Duplicidade de intenção com níveis legítimos de especificidade. Definir herança e preservar mapeamento manual. Nome “existente” não substitui tipologia. |
| Imagem | local comum, raster georreferenciado, web, mosaico/caches/blocos | Fontes versus derivados. Unificar seleção/prioridade, manter originais/resolução e caches persistentes. |
| Estado da edição | `cfg`, `M`, valores DOM, rascunhos de diálogos, epoch/config_revision | Cópias temporárias necessárias, mas com protocolos diferentes. Usar contexto+revisão, aplicação atômica e um rascunho por documento; evitar formulário antigo sobrescrever coleção recente. |
| Estado da tarefa | task local, fila75, política76, job API, artefatos/revisões, progresso41 | Complementares; não reduzir tudo a flag “ocupado”. Um estado compartilhado deve distinguir aguardando, executando, acompanhamento perdido, cancelando, concluído e obsoleto. |

## 7. Arquitetura que sustenta a repetição

1. `53_interface_estudos.js` monta menus a partir de `RIBBON`, `MENUBAR` e `TOOLS`. `75_operacao_consolidada.js` reorganiza os grupos em cinco abas. Módulos posteriores adicionam ações. Não existe um único catálogo autoritativo de apresentação.
2. `modelGroups()` usa “Outras ferramentas” para ferramentas não classificadas. Novas ferramentas de nós/arrasto surgiram no menu Editar por essa regra, apesar da localização correta na faixa Tráfego.
3. `51_shell_profissional.js` mantém catálogo de ribbon legado usado para gerar menus, mesmo quando a faixa final já foi substituída. **Não é seguro apagar esse módulo ou RIBBON por parecer antigo**.
4. Há pelo menos dois contratos gerais de edição: `RodoviaPanels` (59) move campos existentes, captura cfg/M/DOM/histórico e restaura; `RodoviaModelDialog` (64) usa formulário em rascunho e callback. Catálogo63, assistente77, consulta83 e diagnósticos têm contratos próprios. Diferentes necessidades existem, mas a confirmação/fechamento e bloqueio ocupado devem ser comuns.
5. `save`, `load`, `start`, `draw`, `collect`, `showProps/showSegProps` recebem extensões em vários módulos. Isso não comprova execução duplicada, mas torna ordem e efeitos difíceis de rastrear. O registro de ciclo de vida já existente deve ser expandido gradualmente, preservando contratos.
6. `80_cad_compacto.js` cria favoritos que chamam o botão original: duplicação visual intencional e útil, não segunda implementação. Preservar modo compacto e até oito favoritos.
7. A política76 faz abrir/salvar projeto/prévia/vídeo conferirem/atualizarem; o `save()` de persistência é outra operação. Mensagens antigas em56/75 podem dar ideia divergente sobre salvar/cálculo. Consolidar vocabulário sem alterar a política autorizada pelo usuário.
8. `regenScreen()` limpa `tiles`, índices snap e vetores. Não deve ser o remédio padrão para “não vejo veículos”. Redesenhar, atualizar modelo e reconstruir integralmente precisam de nomes e comandos separados.

## 8. Proposta de organização preservando atalhos rápidos

- **Projeto:** identidade, arquivos, CRS, imagens, camadas/classificação e estaqueamento.
- **Editar:** selecionar, mover/copiar/girar/escala/offset/apagar, pontos/recorte geométrico e histórico.
- **Tráfego:** Eixos e sentidos; Seções; Nós; Testar/atualizar; Diagnóstico. Ícones de inserir/editar/mover/apagar nó e reversão continuam acessíveis em grupos compactos.
- **Cena:** áreas/estruturas; materiais; vegetação; iluminação; terreno; 2D/3D. Visibilidade não altera classificação física.
- **Vídeo:** câmera; perfil/qualidade; prévia; exportar; resultados. Tráfego e materiais exibem resumos com links para o editor principal.
- **Faixa fixa compacta:** selecionar/pan, zoom, enquadrar, desfazer/refazer e favoritos. Progresso/atualizar no rodapé. Sem aba Todas e sem um botão por acesso de assistência.
- **Assistência contextual única:** Diagnóstico → Localizar → Propor → Conferir → Aplicar → Revalidar → Desfazer. Regras locais padrão; exportar/importar ou API opcionais.

## 9. Sequência segura de trabalho sugerida

1. Registrar comandos com ID estável, alvo, grupo, ícone, disponibilidade e efeitos; menu/ribbon/contexto/favoritos delegam ao mesmo comando. Primeiro corrigir duplicatas do próprio Editar e “Outras ferramentas”.
2. Usar formulário de nós86 também para Criar ligação de ramal/Forçar ligação; reaproveitar conexões existentes e proibições persistentes. Um editor para campos de sentido/extremos.
3. Colocar diagnósticos70/71/79/82/84/87 na mesma central, sem eliminar análise por classe, visibilidade, arrasto ou prévia revalidada. Localização não dispara cálculo.
4. Consolidar seção típica e informar precedência sobre `sections`/faixas legadas. Só migrar dados com comparação de faixas/itinerários antes/depois.
5. Consolidar catálogo/perfis63/77 e herança de materiais; central de imagens única. Preservar materiais manuais e classificação física separada.
6. Compartilhar protocolo de rascunho/salvar/descartar/fechar com revisão/contexto; não simplesmente trocar todos os diálogos pelo mesmo HTML.
7. Remover apenas exposições redundantes; só arquivar implementação comprovadamente substituída após verificar chamadas dinâmicas, rotas e workers.

Aceitação da futura revisão: mesma ação por menu/ícone/teclado produz o mesmo resultado e uma única tarefa; nós e sentidos salvos/reabertos; off/deny/cortes preservados; seção e material efetivos visíveis; nenhuma edição perdida entre janelas; nenhuma função de segurança removida; navegação não recompila; vídeo de regressão decodificado; interface em janela pequena. A redução de tempo/memória deve ser medida, não inferida da contagem de botões.

## Evidências e limites finais

`interface-executada.json`: controles, handlers, campos, abas, menus reais e registros. `controles-html.json`: origem estática. `referencias-javascript.json`: locais de eventos/extensões. CSVs e `INVENTARIO.md`: navegação nominal de cada item coletado. A auditoria aponta sobreposição e riscos; não afirma que cada botão foi acionado funcionalmente, que todos os popups foram exercitados nem que removeu duplicidades nesta etapa. Nenhum novo ZIP ou alteração de revisão foi feito.
