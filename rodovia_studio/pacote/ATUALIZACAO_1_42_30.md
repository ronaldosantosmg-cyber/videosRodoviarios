# Rodovia Studio 1.42.30 — regras e operação dos fluxos

## Uso

Atualize pelo próprio aplicativo, preservando projetos e vídeos. Abra **Tráfego → Regras e operação dos fluxos** (também comando **REGRASFLUXO** ou **RAMAIS**).

1. Confira o eixo e a seção típica. Linhas de bordo/referência e contornos decorativos não viram obstáculos físicos; canteiros e barreiras classificados continuam limitando a trajetória.
2. A entrada longitudinal padrão é **5 m para dentro do início do itinerário**, conforme confirmado pelo usuário. O motor verifica também se essa inserção não ultrapassa uma retenção vermelha/ferroviária.
3. Escolha o modo de demanda: densidade existente, demanda horária por faixa existente ou VDM do conjunto de entradas. VDM × fração horária determina a demanda horária; a parcela direcional é repartida entre as entradas de cada sentido. Em rede com um único sentido, toda a demanda vai para esse sentido. O campo direcional refere-se ao sentido dos pontos do eixo; confira o estaqueamento se ele cresce no sentido oposto. Editar densidade ou demanda horária encerra o modo VDM, explicitamente indicado na interface.
4. As caixas Somente simular rotas, Proibir travessias do canteiro, Respeitar semáforos e Verificação completa de colisões são independentes. Somente rotas mantém um veículo por itinerário habilitado por vez, reinserindo após a saída, sem aquecimento nem mudança de faixa: serve para conferir trajetórias, não para medir proporções da demanda. Não desliga as demais proteções. Aplicar usa o motor Simulado; Anterior continua disponível para compatibilidade.
5. Aplicar e salvar confirma os parâmetros; Aplicar e calcular os envia ao motor e atualiza os resultados. Fechar permite continuar, salvar ou descartar sem perder o rascunho. A última vista utilizável permanece quando há erro de configuração ou ligação recusada.

## Conexões, ramais e incorporação

Use a ferramenta existente de ligar movimentos no menu Tráfego: clique no trecho de chegada e no de saída. Para um ramal maior, desenhe ou selecione seu alinhamento e configure a seção; depois conecte suas extremidades. O comando não cria uma ligação impossível nem força passagem através de barreiras ou em níveis diferentes.

Nos contatos com espaço real, o motor tenta uma curva tangente e recua localmente a entrada/saída da curva, sem alterar o DXF. Itinerários usam esses recuos; a ocupação de trechos compartilhados mantém a referência física para seguimento e incorporação. Os veículos recebidos não são duplicados como outra corrente na mesma entrada.

O padrão é **80% para a continuidade principal e 20% para os ramais secundários**, repartidos entre eles. A continuidade da mesma via e o comprimento dos eixos orientam a escolha padrão; cada ligação cadastrada pode receber percentual próprio. Deixe o campo da ligação vazio para usar o padrão. Percentuais incompatíveis são recusados com orientação; uma saída única não pode receber 20% sem existir a outra saída. Um movimento com 0% não recebe veículos automaticamente por desvio.

Adicionar ramal não duplica a demanda de densidade na entrada. Na fila, a escolha ponderada fica retida até a admissão, evitando favorecer sempre o primeiro índice. A via maior tem prioridade heurística na incorporação entre vias de mesma classe; semáforos, espaço disponível e proteções continuam valendo. Esta heurística exige conferência técnica; não é reconhecimento automático de toda a regulamentação de prioridade.

Os percentuais são probabilidades de escolha. Vídeos curtos e situações com retenção não garantem contagens exatamente 80/20. O relatório registra demanda, parcelas, contagens admitidas e o fato de incluir aquecimento quando ativo. VDM, PCU e comparação demanda/capacidade não constituem classificação DNIT/HCM certificada.

## Frota e proteção

O perfil **Engenharia** é opcional e preserva os perfis anteriores dos projetos existentes:

- leves: 2 × 6 m;
- motos: 0,5 × 2 m;
- caminhões: 3 × 18 m;
- longos: 3 × 30 m; ônibus mantêm a categoria existente.

Os mesmos comprimentos/larguras alimentam o corpo matemático, o 2D, o 3D e o vídeo. O longo de 30 m é **envelope rígido conservador**, não composição articulada homologada. Pode ser recusado em curvas onde o corpo não caiba; a aplicação não libera a rota apenas para suprimir o aviso.

Mantidos 30 cm livres de distância lateral entre veículos, seguimento mínimo de 2 m, setas nas mudanças/afastamento e retorno e pisca-alerta nas situações de risco/interdição já implementadas. A velocidade acompanha a curvatura e a resolução dos conflitos; não se usa um ângulo isolado de 80°/90° como prova de ausência de colisão.

A sondagem da 1.42.29 permanece: afastamento local de pesados até 1 m além do bordo da pista, independente da hachura/largura do acostamento, com retorno e varredura do corpo. Não foi criada uma faixa contínua de ultrapassagem pelo acostamento.

Desligar a verificação completa entre veículos não desliga as reservas de pedestres, obras ou ferrovia, nem o seguimento longitudinal. Desligar semáforos não elimina sua representação. Saídas com controles desativados são identificadas como **ENSAIO** no 2D, no estado do 3D e nas capturas 3D; não são declaradas livres de colisões verificadas.

## OAE, pavimento e segmentos desconectados

A cota Z do DXF é preservada, sem atribuir altura fictícia de 5 m. OAE com Z=0 não cria barreira por seus contornos. Estrutura longitudinal não bloqueia a continuidade da via por suas linhas. OAE transversal em Z=0 recebe orientação para conferir a cota, sem inventar desnível ou deixar vermelho um itinerário válido.

Uma cota CAD não nula pode ser absoluta: ela sozinha não libera uma travessia ferroviária. Cadastre/confirme o desnível relativo na OAE. Para OAE em nível diferente confirmado, tanto a retenção quanto a reserva do trem respeitam a separação de níveis. Sem confirmação, as proteções reais de travessia continuam ativas.

Em **Autorização individual de eixos sem pavimento**, marque somente os alinhamentos com seção conferida. O corredor usa as faixas da seção, exclui barreiras/canteiros e não usa toda a largura do acostamento. Isso não reativa rotas desligadas nem autoriza todas as linhas do desenho. Para eixo DXF, primeiro use Escolher eixo e configurar faixas.

Em **Excluir segmentos desconectados**, selecione os trechos do diagnóstico atual e confirme. A exclusão é da circulação: o DXF e a geometria original são preservados. Desfazer e o histórico permanecem disponíveis. Fluxos independentes abaixo do limite do projeto continuam sem circulação; pequenos elementos internos necessários à continuidade permanecem.

## Entrega e limites

ZIP exclusivamente em atualizacoes/, sem sobrescrever históricos. Preservados projetos/, videos/, fontes DXF/KMZ, imagens originais, cache persistente GeoTIFF, snapshots, fechamento controlado e rollback. Main não alterada.

Evidências desta revisão: evidencias/1.42.30. Testes dirigidos não equivalem à suíte histórica completa, uso prolongado no Windows do usuário, homologação CONTRAN, calibração de tráfego ou qualidade equivalente a Twinmotion. Não se afirma ausência universal de travamentos ou colisões.

## Complemento: o próprio pesado ultrapassa

Em **Tráfego → Regras e operação dos fluxos**, a opção **Ensaio: o próprio pesado ultrapassa pelo acostamento** permite a saída à direita, passagem de veículo mais lento e retorno à faixa de origem. É uma manobra opcional de estudo, desativada por padrão, identificada como ENSAIO na apresentação. Não constitui autorização normativa para ultrapassar pelo acostamento.

O corpo inteiro e a varredura devem caber na superfície disponível, limitada a 1 m além do pavimento; a largura do acostamento não é convertida em faixa adicional. Outra faixa cadastrada à direita impede essa manobra. A passagem exige diferença de velocidade, distância para a saída e retorno, ausência de conflito previsto com os veículos próximos e preserva as reservas espaciais por passo, semáforos, obras, pessoas e trens. Se faltar espaço, o pesado aguarda. O modo somente rotas e a desativação da reserva de colisões impedem a ultrapassagem.

Exemplo de recusa necessária: 3 m de pesado + 2 m de carro + 0,30 m de folga exigem 5,30 m de largura simultânea; uma única faixa de 3,60 m acrescida de 1 m não oferece essa largura. Mudanças imprevistas podem interromper a manobra; a previsão não garante que toda ultrapassagem será completada, nem substitui dinâmica articulada ou calibração de tráfego.
