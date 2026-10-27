# Validação dirigida — Rodovia Studio 1.42.36

Base 1.42.35, branch desenvolvimento/rodovia-studio-1.42. Data 27/10/2026. 136 testes únicos aprovados na seleção final, sem falhas ou ignorados. Ver pytest-direcionado.xml e consolidacao_testes.json para a deduplicação e a origem. Núcleo final: 119 testes; regressões UI/integradas: 17 casos únicos, com casos afetados repetidos após os ajustes finais. Não foi executada a suíte histórica completa nem homologação nativa Windows/8 GB.

## Comportamentos verificados

- Sentido e desligamento nativos ligados à impressão da geometria/camada, sem transferir decisões quando a lista CAD muda de ordem.
- Fonte com impressão alterada e desligamento anterior permanece pendente, em vez de ser reativada silenciosamente. Índices legados não são migrados por adivinhação.
- Reversão explícita de alinhamento e nós de entrada/saída, mantendo coordenadas e desligamento manual.
- Botões existentes de inserir/selecionar/editar/mover/apagar nós e classificação de extremos preservados, com regressão de gravação e desfazer.
- Compatibilidade por classe usando a decisão de admissão da simulação; ensaio de curva R=15 m aceita leve e recusa longo rígido, sem mover o eixo ou liberar a classe recusada.
- Teste de circulação de até 10 s com resultado e imagem separados, assinatura de fonte/configuração/código e rejeição de resultado antigo.
- Retomar acompanhamento consulta a tarefa existente após perda de conexão; não cria outro cálculo. Ajuste DXF/imagem descarta resposta fora de contexto.
- OAE com Z=0 não cria barreira/desnível nem emite a antiga orientação de sentido. O sentido explícito do eixo tem prioridade. OAE com desnível relativo confirmado conserva suas regras, inclusive travessia ferroviária; barreiras/canteiros reais permanecem.
- Integração DXF com duas linhas OAE (transversal e longitudinal) e hachura de OAE em Z=0 preserva itinerários e veículos; a condição esperada passa a informação técnica, não aviso genérico de erro.
- Vídeos protegidos e clássico gerados/decodificados nos testes dirigidos; nós, conservação de demanda, colisões e ferramentas de arrasto preservados nos cenários testados.

## Evidência de fonte real

DXF DUPLICAÇÃO TH53 fornecido: 31 eixos geométricos, 7 itinerários revalidados; em t=1 s, 6 veículos ativos, 2 desenhados no recorte e 4 fora da vista, sem corpo fora da superfície nesse instante. Camadas explicitamente cadastradas no ensaio; original preservado. Ver dxf_real.json e imagem correspondente. Não é o projeto salvo atual do usuário, nem garantia universal de ausência de conflitos. Não houve benchmark controlado de desempenho nesta revisão.

## Limitações e pendências

- Impressão depende da geometria/camada/cota de referência, não é um kernel CAD nem migração automática universal de toda edição. Fonte modificada exige conferência.
- A análise explícita por frota tem orçamento de 300 itinerários e informa quando parcial. O desenho normal reutiliza as auditorias de tipos já tentados, sem auditar toda a frota a cada quadro.
- Longos são corpos rígidos conservadores, sem homologação articulada.
- O clássico é ensaio; não valida colisões, pessoas, sinais, barreiras e interdições. Não é usado para remover avisos do modo protegido.
- O teste curto não substitui a validação do vídeo completo nem classifica nível de serviço DNIT/CONTRAN.
- Não foi reproduzido integralmente o projeto salvo do usuário; contornos classificados erroneamente como Barreira/Canteiro precisam de classificação correta, não de uma liberação geral por nome.
- Modelo/runtime 3B real, API real e uso prolongado Windows/WebView2/8 GB continuam pendentes.
- Testes intermediários tiveram erros de preparação das novas amostras (set em vez de lista, dicionário em vez de modelo validado) e dois testes históricos dependiam de índices posicionais. As amostras foram corrigidas e os contratos atualizados para chave estável. Somente rodadas finais aprovadas entram na consolidação.

Iniciador C# e splash conferidos em Mono/Xvfb; não é teste Windows nativo. O relatório de aplicação/rollback do pacote é produzido depois do ZIP e fica no repositório para evitar uma referência circular ao hash do próprio arquivo.

Prontidão estimada: 7,8/10 para uso intenso, com avanço dirigido em fluxos e limites de homologação mantidos. Não é certificação nem nota aumentada apenas por quantidade de testes.

## Compatibilidade ao voltar de versão

Esquema de configuração 31 protege os vínculos de sentido. A 1.42.35 (esquema 30) rejeita configurações novas, em vez de ignorar silenciosamente sentidos/desligamentos. Rollback do programa preserva dados, mas abrir na versão antiga exige a cópia de configuração/projeto anterior à atualização. O teste de compatibilidade usa o código de migração efetivamente incluído no ZIP histórico 1.42.35.
