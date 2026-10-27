# Evolução dos fluxos e proposta de simplificação

Base: código 1.42.35, commit 3322040, histórico Git e solicitações do usuário. Análise em 27/10/2026. Não altera o aplicativo. Não reproduz integralmente o projeto salvo atual do usuário.

## Conclusão

Acrescentamos geração de faixas, geometria corporal, recuperação, nós, demanda, controle de conflitos e diagnóstico. A dificuldade atual não se resolve acrescentando mais seletores nem desligando todas as verificações. Falta consolidar um contrato de circulação entre cadastro, itinerário, frota, simulação e apresentação, com uma ação específica para cada causa e uma forma de corrigir o eixo original mesmo quando não existe trajetória calculada.

## Evolução comprovada no histórico

- **1.39:** referência de operação e botões indicada pelo usuário. Não foi revalidada nesta análise como versão livre de falhas.
- **1.42.2–1.42.6:** restauração de comandos, destaque de fluxos, filtro de pequenos itinerários, validação de movimento e integração de ferrovia/semáforos e filas.
- **1.42.7–1.42.10:** preservação de edições concorrentes, catálogo CAD, ferramentas de recortar/juntar e controles de transporte.
- **1.42.12–1.42.18:** continuidade DXF, localizar bloqueios, recuperação de partes válidas, orientação local, central de correção e restrição às fontes de eixo/sentido por intervalo.
- **1.42.19–1.42.23:** correções de densidade, seção típica pelo eixo, cache por rota, separação entre ligação recusada e circulação válida e política de atualização.
- **1.42.24–1.42.28:** assistência de regras/propostas revisáveis, diagnóstico amarelo e revisão da apresentação de veículos. Modelo 3B real não homologado.
- **1.42.29–1.42.31:** sondagem local de pesados, larguras/comprimentos e folgas atualizados, entrada recuada, controles individuais, VDM e nós. Categoria de acesso com 5% e retornos/dispositivos/rotatórias com 20%, como totais repartidos entre ramais, preservando conservação de fluxo e entradas externas cadastradas.
- **1.42.32–1.42.33:** confirmação de formulários e redução de leitura/repreparação do DXF.
- **1.42.34:** botões para inserir/selecionar/editar/mover/apagar nós, extremos de entrada/saída/fim, recuo nas duas pontas do pavimento, modo clássico ilustrativo e inspeção de arrasto fora do vídeo.
- **1.42.35:** fonte explícita obrigatória, isolamento de destaques/projetos, conciliação de gravação, cancelamento/supervisão e atualização incremental.

Essas entregas não equivalem a reconstrução automática de qualquer ligação defeituosa, CAD completo, validação normativa ou funcionamento comprovado no projeto salvo do usuário. Os testes de cada entrega tinham cenários e limites específicos.

## Por que um fluxo pode continuar sem veículos

### Há várias etapas de aprovação

1. Fonte aceita/cadastrada e sentido configurado.
2. Seção e faixa operacional, área de circulação reconhecida.
3. Conexões, continuidade, entradas/saídas e comprimento mínimo.
4. Geometria do itinerário: centros, corpo, curva e mudanças de rumo.
5. Admissão por tipo de veículo e controles dinâmicos: outras pessoas/veículos, semáforo, interdição, ferrovia e demanda.
6. Apresentação: enquadramento, revelação progressiva e verificação do corpo antes de desenhar.

São responsabilidades diferentes, mas hoje seus resultados não formam sempre uma explicação única acionável. Aumentar densidade não resolve falta de itinerário; recortar não corrige pavimento mal classificado; corrigir um eixo não altera um sinal fechado ou enquadramento errado.

### Verde não significa que toda a frota cabe

`traffic.py` usa verificações de centros e uma auditoria geométrica básica na formação de itinerários. `simulation.motion_valid` revalida cada tipo real. `render.fits` verifica o corpo antes de desenhar. A primeira aprovação pode não representar a aprovação de um pesado de 18/30 m.

Ensaio atual, sem alterar o código: curva sintética de raio 15 m, faixa central cadastrada e corredor de 7,2 m. Resultado: 1 itinerário; diagnóstico geométrico ok; leve car6 aprovado; longo long30 recusado. JSON ao lado. Isso não é falso bloqueio do longo: mostra que o diagnóstico precisa distinguir compatibilidade por frota e localizar o motivo. Não foi reproduzido o projeto salvo do usuário.

Há parâmetros históricos diferentes nas etapas (por exemplo valid_centers possui dimensões padrão distintas dos perfis de frota). Não são todos redundantes: uma aproximação de pré-seleção e a conferência corporal podem ter papéis legítimos. O problema é não declarar essas etapas claramente e não compartilhar um contrato de perfil, superfície e revisão. Consolidar parâmetros, não simplesmente apagar a última proteção.

### A correção depende por vezes do resultado que faltou

Os comandos de recorte/junção e nós trabalham principalmente sobre segmentos do editor. Uma fonte ignorada por falta de cadastro ou descartada antes de compor segmentos pode não oferecer seleção na própria central de fluxos. É necessário permitir diagnosticar/corrigir a fonte CAD ou o alinhamento cadastrado independentemente da existência de veículos ou de um itinerário final.

### Um defeito local pode reprovar um percurso completo

`make_itineraries` audita o percurso montado; a recusa registra a sequência de arestas. Um bloqueio real local pode impedir o percurso inteiro, sem significar que toda sua extensão esteja geometricamente defeituosa. A apresentação deve separar “ponto causal” de “trechos sem passagem por consequência”. Recuperar partes válidas não garante ligar entrada a saída.

### A rede depende de dados operacionais persistentes

A análise posterior à 1.42.35 demonstrou que route_directions ainda pode acompanhar índice de eixo; alteração da ordem CAD pode transferir sentido/desligamento. Isso deve ser resolvido antes de exigir que o usuário redesenhe o traçado. Também persistem oportunidades de recuperar acompanhamento de tarefas e proteger outros comandos contra respostas atrasadas.

## Simplificação proposta — usa o motor existente

### Quatro ações principais

1. **Cadastrar eixo:** selecionar fonte no desenho, confirmar identidade, sentido crescente e estaqueamento. Cadastro e seleção continuam funcionando sem fluxo calculado.
2. **Configurar circulação:** uma janela com seção, faixas ativas, sentidos e frota. Uma escolha explícita entre densidade visual e demanda/VDM, evitando modos que mudam sem o usuário perceber.
3. **Testar e corrigir:** prévia curta independente do vídeo final, contador de veículos e relatório por eixo/faixa/tipo. Localizar e agir sobre a causa, testar novamente só a dependência alterada.
4. **Gerar vídeo:** usar a configuração testada, conferir a revisão, enquadramento e presença dos veículos. Não exigir que uma tentativa de ligação opcional recusada bloqueie os itinerários válidos.

### Perfis compreensíveis

- **Apresentação de tráfego:** movimento por faixas cadastradas; comportamento mais simples e previsível, sem manobras experimentais por padrão. Preservar colisões, canteiros/barreiras e controles físicos configurados. Declarar caráter ilustrativo, sem resultados de capacidade apresentados como estudo validado.
- **Simulação técnica:** demanda/VDM, filas, repartições em nós e demais recursos avançados, com parâmetros explícitos e relatório.
- **Clássico existente:** manter recolhido como ensaio de diagnóstico. Ele verifica somente canteiros/integridade numérica e não substitui o perfil protegido. Não resolve por si só ausência de eixo, itinerário, demanda, portal ou enquadramento.

Esses perfis são proposta, não recursos novos já entregues. Implementar como configuração coerente dos componentes existentes, sem outro simulador paralelo. Não mudar silenciosamente a frota ou ignorar semáforos, barreiras e interdições cadastradas para fazer veículos aparecerem.

### Uma central que leva o problema até uma ação verificável

| Causa | Ação principal |
|---|---|
| Eixo não cadastrado | Selecionar e cadastrar a própria fonte |
| Sentido/identidade divergente após importação | Conferir vínculo estável e sentido |
| Seção ausente ou incompleta | Editar a seção no intervalo localizado |
| Pavimento não reconhecido | Corrigir classe ou confirmar corredor da seção onde ele existe fisicamente |
| Afastamento excessivo | Ajustar dentro da faixa e revalidar corpos |
| Conexão opcional recusada | Preservar principal válida; localizar/corrigir apenas a ligação |
| Pequena lacuna, duplicata ou ruído | Prévia de limpeza derivada com tolerância limitada e validação |
| Curva incompatível com um tipo | Mostrar tipo e ponto, editar curva ou solicitar escolha explícita da frota |
| Barreira/canteiro/interdição | Manter impedimento e oferecer rota alternativa válida/pare e siga cadastrado |
| Semáforo fechado ou ferrovia ativa | Mostrar espera/fila e fase, sem rotular como geometria inválida |
| Desligamento manual ou abaixo do limite | Estado desativado/ignorado, preservado; não erro genérico |
| Sem veículos por demanda/instante | Ajustar demanda e período de observação, sem alterar o eixo |
| Veículos fora da imagem ou muito pequenos | Ajustar câmera/escala, sem reconstruir a rede |
| Dados antigos ou tarefa sem acompanhamento | Atualizar dependências/retomar a tarefa, sem refazer cadastro |

Para cada item: fonte e revisão, coordenada/estaca, evidência, veículos afetados, ferramenta direta, prévia da alteração, Aplicar/Cancelar e Desfazer. Quando não for corrigível automaticamente, explicar exatamente o que falta e permitir editar a fonte. O sistema especialista local é suficiente para essa associação; um LLM não deve ser requisito para usar os fluxos.

### Cores e estados

- Verde: circulação realmente disponível para a configuração/frota declarada.
- Amarelo: restrição parcial, aviso ou incompatibilidade explicitamente identificada; mostrar quais tipos/faixas continuam aptos.
- Vermelho: impedimento real da circulação solicitada, com localização causal.
- Cinza: desativação manual, itinerário independente abaixo do limite ou fonte não incluída.
- Processando/desatualizado: estado separado das cores de impedimento.

Um sinal vermelho exige parada operacional, mas não torna o eixo geometricamente errado. Uma rota válida pode estar momentaneamente sem veículos. Evitar confundir essas situações na interface.

## O que simplificar internamente

- Cadastro de fonte com identidade estável e migração conferida de índices antigos.
- Um contrato de validação por eixo/faixa/tipo de veículo, superfície operacional e revisão; resultados compartilhados entre editor, simulação e desenho.
- A última conferência gráfica deve denunciar divergência com a simulação, em vez de apenas ocultar o corpo sem uma ação acessível. Não removê-la antes de demonstrar equivalência.
- Corrigir o trecho causal na derivação editável, preservando CAD, nós válidos, decisões manuais e continuidade verificável entre origem e destino.
- Separar falha física permanente de espera operacional e condição de enquadramento/demanda.
- Manter ferramentas avançadas de recorte/junção/recuperação, mas reunir suas entradas na central principal.
- Centralizar larguras, comprimentos, entre-eixos e folgas nos perfis já existentes, eliminando divergências históricas por migração e testes.
- Não gerar trajetórias a partir de qualquer hachura/linha nem liberar travessias reais para remover vermelho.

## Ordem sugerida e aceitação

1. Identidade estável + diagnóstico completo desde a fonte, mesmo sem itinerário.
2. Contrato comum de frota/superfície e localização de recusas por classe.
3. Central causa→ação, estados de espera/desligamento e correção derivada reversível.
4. Quatro ações de operação e perfis simples/técnico com prévia curta.
5. Regredir exportação 2D/3D e homologar no projeto salvo problemático do usuário.

Cenários: eixo reto sem hachura com seção confirmada; pista simples e dupla; curva que aceita leves e recusa longos; acesso/retorno; barreira verdadeira; linha decorativa perpendicular; semáforo fechado/aberto; pare e siga; alteração da ordem CAD; desligamento manual; demanda pequena; veículo fora de câmera. Verificar MP4 decodificado e presença/contagem por etapa. Não aprovar apenas porque uma rota ficou verde.

A questão principal não é voltar integralmente à 1.39 ou adicionar outra IA: é fazer as ferramentas existentes fecharem o ciclo “identificar → corrigir → testar → gerar”. Nenhuma dessas propostas de consolidação foi implementada por esta análise, e nenhum novo ZIP foi gerado.
