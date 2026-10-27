# Análise posterior à 1.42.35

27/10/2026. Código na branch desenvolvimento/rodovia-studio-1.42, base 3322040. Nenhuma função, pacote ou main alterados nesta análise. Análise dos caminhos principais e ensaios isolados, não auditoria exaustiva de cada função nem homologação Windows. Os 100 testes da entrega anterior continuam sendo evidência daquela seleção; não foram repetidos aqui e não cobriam todos os casos abaixo.

## Achados reproduzidos

### 1. Prioridade crítica: identificação estável dos eixos

`app/native_axes.py` consulta `settings.route_directions[str(i)]`, em que i é a posição do eixo recebido. Em `geometry.py`, eixos são ordenados por comprimento. Inserir/remover/alterar comprimentos no CAD pode mudar essa posição.

Ensaio com dois eixos cadastrados: posição 0 desligada, posição 1 crescente. Antes de inverter a lista, o eixo habilitado tinha Y=20; depois da inversão, Y=0. A decisão acompanhou o índice, não a identidade física. Isso não prova que ocorreu no projeto salvo do usuário, mas confirma a fragilidade do contrato.

Melhoria: persistir sentido e desligamento por identificador de fonte verificável, combinando arquivo, entidade/handle e impressão geométrica. Preservar o contrato de alinhamentos e as chaves de cortes/nós existentes. Migrar índices antigos com conferência; se a correspondência for ambígua, pedir revisão, sem habilitar ou transferir um desligamento silenciosamente. Testar reordenação, substituição de arquivo e alteração geométrica legítima. Não confiar apenas no handle sem associá-lo à fonte.

### 2. Prioridade alta: recuperação do acompanhamento de tarefas

`app/js/07_tarefas_intervencoes.js`, função poll: ao falhar a consulta de estado, a exceção sai do laço sem limpar/reconciliar task. start libera taskRequestPending em finally, mas a variável task continua preenchida. Um novo comando pode ser recusado como se a operação ainda estivesse ocupando a interface, mesmo que o servidor tenha concluído.

Ensaio da função original com API indisponível: task permaneceu tarefa-a. O botão Cancelar continuou disponível; portanto, não afirmar bloqueio irrecuperável ou falha do motor.

Melhoria: estado explícito “conexão interrompida, situação da tarefa desconhecida”, reconexão limitada com espera progressiva, botão Retomar acompanhamento e conciliação pelo ID. Não limpar a tarefa presumindo que acabou nem reenviar o cálculo automaticamente. Revalidar projeto/contexto ao receber o estado.

### 3. Prioridade alta: respostas atrasadas fora dos fluxos já protegidos

fitAlign, no mesmo arquivo JS, aplica alignResult depois do await sem conferir projeto/contexto ou revisão dos pares. Ensaio isolado: foi possível alterar o contexto antes de resolver a API e o resultado antigo foi aplicado. A 1.42.35 protegeu camadas/faixas/destaques, mas isso não cobre automaticamente todos os comandos assíncronos.

Melhoria: generalizar o contrato de tarefa com projeto, contexto, token e assinatura dos dados de entrada. Estender a conferência a ajuste DXF/imagem, busca de cidades, sessões e validação de ferrovia/semáforo. Não declarar que todos esses caminhos têm o mesmo defeito sem ensaio específico; são candidatos de revisão. Testar também mudança de parâmetros dentro do mesmo projeto.

### 4. Prioridade alta: memória mínima antes de preparar a cena

parallel.plan_workers limita a quantidade de processos, porém o piso é sempre 1. Com apenas 256 MiB disponíveis e exportação 4K, a função ainda retornou 1. A escolha dos trabalhadores ocorre depois da preparação de Scene, portanto não impede que a própria preparação consuma memória excessiva.

Melhoria: verificação prévia de memória/complexidade antes da cena, qualidade de navegação separada da exportação, teto agregado para imagens/caches/3D/IA e opção de reduzir qualidade ou adiar. A estimativa não deve ser apresentada como quota garantida. Medir no Windows/8 GB, incluindo pressão real de memória e comportamento de drivers.

### 5. Prioridade média: tornar o estado de proteção de dados mais específico

project_integrity.inspect verifica configuração, histórico e presença de fontes; não abre semanticamente DXF/KMZ/imagens, conforme seu próprio campo scope. Ensaio: arquivo não vazio chamado input.dxf com conteúdo inválido, configuração válida, estado retornado integro. Isso não significa que o leitor CAD aceite o arquivo; a inspeção tem escopo mais estreito.

Melhoria: separar “configuração íntegra”, “fontes presentes” e “fontes validadas pelo leitor”, com data/revisão da última leitura bem-sucedida. Hashes e verificação incremental podem detectar alteração posterior, sem reler arquivos grandes em cada clique. Não substituir arquivo inválido por um vazio nem apagar bytes defeituosos. Acrescentar cópia portátil de segurança do projeto com manifesto, se entrar no escopo de implementação.

## Oportunidades que exigem validação adicional

- **Supervisão de progresso:** o heartbeat sinaliza que a thread Python está viva; não prova que a etapa de cálculo avança. Registrar último avanço real, etapa e contadores, oferecer diagnóstico/cancelamento e usar prazos por operação, evitando matar cálculos longos válidos só pela duração.
- **Interface:** continuar a migração gradual das extensões globais para serviços/registro comum, com um controlador de transações e recuperação. Evitar uma reescrita geral.
- **Desempenho:** dependencies.engine_revision relê os módulos Python em cada consulta e input_stamps percorre as fontes. Medir a frequência e o custo no Windows/OneDrive/antivírus antes de otimizar. Cachear somente com critério confiável de revisão e sem aceitar resultados obsoletos.
- **Tráfego:** aproveitar o diagnóstico atual para apresentar decisão por eixo/faixa/nó e por fase: cadastrado, calculado, habilitado, com demanda e visível no enquadramento. O contador agregado de veículos já existe; a oportunidade é torná-lo acionável por origem, sem outro motor de regras.
- **Vídeo/3D:** medir orçamento de texturas, descarte de recursos e qualidade em cenas grandes; validar consistência entre prévia, MP4 e 3D, além de uma prévia curta. Não trocar o motor nem prometer qualidade Twinmotion.
- **IA:** aumentar a biblioteca local de causas e ações tipadas, com evidência, prévia e confirmação. O adaptador 3B não equivale a modelo instalado; pesos, latência e memória precisam de homologação. Não permitir scripts arbitrários ou envio automático de dados.
- **Windows/distribuição:** testar caminhos longos, OneDrive, usuário sem administrador, interrupção, bloqueio de arquivos e uso prolongado. Hash SHA-256 não autentica sozinho o publicador; verificar assinatura do manifesto e dos binários. Não recomendar exclusões de antivírus.

## Ordem recomendada

1. Identidade estável de eixo, com migração e preservação dos desligamentos.
2. Recuperação de acompanhamento e contrato único contra respostas atrasadas.
3. Verificação prévia de memória e diagnóstico de fonte validada.
4. Consolidar formulários/serviços e diagnóstico operacional dos fluxos.
5. Homologar Windows/8 GB e cargas prolongadas, depois investir em mais efeitos e IA.

O produto avançou na 1.42.35, mas estes achados impedem recomendar uma nota 9 com base apenas nos testes atuais. Não foi atribuída uma nova nota por esta análise; a estimativa anterior não é certificação.
