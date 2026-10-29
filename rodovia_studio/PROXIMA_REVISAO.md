# Continuidade após a revisão 1.42.36

Fluxos: preservar os nós, as seções, os sentidos por fonte estável e a reversão explícita. Não voltar a usar a posição de um eixo na lista como identidade. Cadastros antigos/alterados ambíguos exigem conferência; desligamentos não são reativados automaticamente.

OAE Z=0: contornos não são impedimento nem fonte de inversão de sentido. Preservar o diagnóstico informativo, os níveis relativos confirmados e os demais bloqueios físicos/dinâmicos. Não desativar barreiras reais só por terem OAE no nome.

Próximos ensaios: projeto salvo atual do usuário, sessões prolongadas Windows/WebView2/8 GB, carga de grande número de fontes e orçamento agregado CPU/GPU/IA. Reverter vias de dois sentidos exige escolha de faixa/seção; não confundir com inverter o estaqueamento ou programar reversão por horário, não implementada nesta revisão.

Consolidar futuramente cadastros/ações ainda duplicados e ampliar correções tipadas, sem outro motor nem código arbitrário de IA. Não prometer reconstrução universal de qualquer ligação ou conformidade normativa. Pesos/runtime 3B real e API real permanecem sem homologação.

Somente branch de desenvolvimento, main protegida, fontes e dados persistentes preservados, testes atuais antes de pacote e ZIPs históricos intactos em atualizacoes/.

## Etapa de desenvolvimento: menus e central de correção

Iniciada a consolidação solicitada (itens 4 e 2 da auditoria). O menu Editar não repete transformações dentro de Propriedades; ações de arquivo ficam em Arquivo. Nós e edição de trechos têm submenu próprio em Tráfego, com Sentidos e nós/Testar circulação explícitos. Botões rápidos e contratos dos nós permanecem.

RodoviaFlowRepair.open encaminha à central baseada na assistência de execução existente; ferramentas antigas ficam em RodoviaFlowRepair.advanced. A central explica passos, propõe antes de aplicar, preserva desligamentos e revalida pelo mesmo motor. Diálogos de modelagem identificam Salvar e fechar / Salvar e atualizar. Janela com rodapé fixo; bloqueio de cliques duplicados e liberação após erro. Não reaplicar proposta já confirmada se a leitura posterior falhar. Receber resultados mantém seleção e não abre Propriedades automaticamente.

Esta etapa não altera versão/schema nem cria novo ZIP. Evidências e limites em evidencias/interface-central/LEIA_ME.md. A reorganização integral de todos os formulários e o registro único de comandos ainda não foram concluídos.

## Continuação de formulários e informações da interface

Confirmação compartilhada em RodoviaDialogDecision para modelagem, catálogo, assistente e conexão. Salvar perfil não aplica no projeto nem recalcula. A faixa preserva ícones/atalhos durante expansão; legenda 2D compartilha estado/paleta com desenho e distingue desligado (cinza), impedido (vermelho), pendente (amarelo), válido (verde). Artefato antigo não aparece como aprovação atual.

Exigência reforçada do usuário: rodapé em uma linha, sem aumentar altura nem tomar área do canvas. A proposta responsiva de duas linhas foi retirada. Corrigir valores/informações, usar indeterminado quando não há medição, explicitar decorrido/estimativa. Evidências em evidencias/formularios-etapa2. Ainda sem ZIP, versão/schema preservados. Próxima etapa: seções/sentidos/nós e restante do cadastro de materiais/layers, depois regressão de vídeo e atualização.

### Vista, prévia e sessões — continuação

Organizados controles existentes em grupos, com opções avançadas recolhidas. Corrigida visibilidade de sessões/navegação no popup, descarte das preferências reais e respostas antigas de sessões após troca de contexto. Mantida barra inferior em uma linha. Evidências consolidadas em evidencias/formularios-etapa2; etapa sem ZIP, exportação MP4 ou homologação Windows.

### Logs de fluxo e imagem combinada

Corrigidos UTF-8 da assistência no Windows, ciclo de falha de prévia sem alvo, recusa explícita de exportação sem itinerários e respostas obsoletas do pincel. Aviso ENSAIO passa a avisos/metadados, sem faixa no vídeo. Imagem combinada pode usar local válida se o mapa web falhar. Ajustado reconhecimento de hachuras de pista; ensaio no DXF disponível passou a 7 itinerários, mantendo trechos recusados. Ver evidencias/correcao-log-fluxos para escopo e limites; não é pacote liberado.


### Entrega 1.42.37 concluída

ZIP novo gerado após aprovação de 961 casos, zero falhas/erros/ignorados, compilação C# e splash. Atualização e rollback do arquivo final conferidos em instalação isolada com preservação de dados. Evidências em evidencias/1.42.37/LEIA_ME.md e entrega-conferida/. As tentativas bloqueadas anteriores permanecem como histórico. Pendências: homologação Windows/WebView2/8 GB, carga prolongada, benchmarks comparáveis e configuração real do projeto do usuário; não inclui pesos de IA 3B. Nota estimada 7,8/10.


### Correção dirigida do acompanhamento — após 1.42.37

Reconexão de leitura sem reenviar o cálculo, espera na fila sem limite arbitrário de dois minutos, Retomar visível no rodapé e eliminação de consultas finais redundantes. A fila aguarda a aplicação do resultado. 18 testes dirigidos aprovados, incluindo perda de conexão no servidor real e confirmação de POST único. Evidências em evidencias/acompanhamento-reconexao/. Sem novo ZIP nem nova aprovação integral; pacote histórico 1.42.37 preservado.


### Entrega 1.42.38 — acompanhamento corrigido e empacotado

A correção antes disponível apenas na branch agora integra um ZIP novo, após aprovação consolidada de 971 casos, splash e compilação C#. Atualização 37 → 38, arquivos corrigidos instalados e rollback para 37 conferidos com preservação de dados de teste. Evidências em evidencias/1.42.38/. A preferência de sempre entregar novo ZIP após correções foi registrada em AGENTS.md; a tentativa anterior sem pacote é histórico. Limites Windows/8 GB/carga prolongada e nota de referência 7,8/10 mantidos.

### Entrega 2.01 — operação e apresentação consolidadas

Versão solicitada pelo usuário, sobre a 1.42.38, sem substituição do motor e com schema 31. Preservação de escala/centro no resize, Aplicar sem fechar com novo ponto de descarte, validação de campos, fila única nos formulários, ordenação das camadas/materiais, contraste/ícones e materiais locais em superfícies 2D. Evidências em evidencias/2.01/LEIA_ME.md.

Aprovação consolidada de 977 casos do mesmo produto (897 preservados, 80 repetidos), splash/C# em Mono/Xvfb. Atualização real do ZIP e rollback para 1.42.38 conferidos com preservação de bytes e restauração de todos os hashes anteriores. HTTPS HTTP 200 e SHA-256 conferidos. Main intacta. Prontidão provisória 6,5/10; Windows/8 GB, projeto real e demais limites constam no relatório. A infraestrutura paralela de testes ainda requer isolamento de banco por worker para evitar interferência entre instâncias; módulos afetados foram repetidos em série.


### Entrega 2.02 — reconstrução integral e continuidade comprovada

Reconstrói a trajetória inteira antes de separar amostras inválidas; busca limitada no corredor físico e validação do percurso. A central exige um itinerário cobrindo todos os subtrechos de cada sentido antes de permitir aplicar. Distingue recuperação parcial, preserva recortes/desligamentos, recusa correção sem efeito e localiza impedimento real. Fonte CAD, nós, seções e motor existente preservados.

Regressão nova: 995 casos (965 do mesmo produto preservados e 30 reexecutados), zero falhas/erros/ignorados no relatório consolidado. Progresso inicial: 994/995; o caso de hachuras teve sua preparação sincronizada com a conclusão do trabalho inicial e passou novamente. C#/splash em Mono/Xvfb; MP4 inteiro decodificado. Perfil artístico existente validado com veículos, materiais naturais e a mesma geometria de cálculo. Não foi criado outro renderizador. Atualização real do ZIP, preservação e rollback 2.01 conferidos; HTTPS HTTP 200 e SHA-256 idênticos. Main intacta. Evidências em evidencias/2.02/LEIA_ME.md. Prontidão provisória 7/10; Windows/8 GB, projeto real e carga prolongada pendentes.
