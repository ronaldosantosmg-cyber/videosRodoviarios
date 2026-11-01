# Rodovia Studio 1.42.34

## Nós e conexões

Na aba Tráfego, a faixa compacta contém Inserir nó de ligação, Selecionar nó, Editar nó, Mover nó de ligação, Apagar nó, Nó de entrada/saída/fim e Inspecionar arrasto. Hover apresenta a função de cada ícone. Os comandos também podem ser chamados como INSERIRNO, EDITARNO, MOVERNO, APAGARNO, ARRASTO e FLUXOCLASSICO.

- Inserir: clique no trecho de chegada e no trecho de saída, perto do encontro, e confirme nome/percentual. Alterações só entram no cadastro após aplicar/salvar ou aplicar/calcular.
- Nós automáticos entre eixos diferentes também aparecem em planta e podem receber uma regra explícita.
- Apagar ligação registra uma proibição persistente, preservando eixos e faixas; a detecção automática não deve recriar o movimento. Editar permite conectar novamente. Apagar um nó de extremidade devolve sua classificação a Automático.
- Mover altera os pontos que identificam os trechos da ligação, sem deformar os eixos. Para deslocar fisicamente um extremo do alinhamento, use a edição por pontos de controle. Entrada/saída/fim acompanham os extremos A/B cadastrados.
- As regras novas vinculam os identificadores geométricos de origem e destino; não devem trocar de eixo silenciosamente quando houver linhas próximas.
- Nós, seções, percentuais e setas continuam no mesmo motor de cálculo, prévia e vídeo. Não há um segundo cadastro independente de rede.

## Contato de retorno e portais externos

O ramal com faixas cadastradas pode dividir o eixo principal no ponto de contato. Uma pequena diferença lateral entre faixas paralelas recebe uma transição tangente conferida no pavimento, em vez de uma emenda curta e brusca. Níveis diferentes não ganham conexão plana.

O recuo configurado (padrão 5 m) é aplicado às duas pontas externas do itinerário, considerando o pavimento mesmo quando o eixo ultrapassa seu limite. As conexões internas dos nós não recebem esse corte. A simulação não soma outro recuo à entrada já ajustada. Corpos longos continuam sujeitos ao espaço efetivamente disponível no modo protegido.

## Motor clássico ilustrativo

O botão Modo clássico de fluxo abre uma seleção explícita. Nesse modo, a rede apresenta veículos com a densidade configurada, conferindo canteiros e integridade numérica. Desativa verificações operacionais de colisões, semáforos, pessoas, barreiras, obras e ferrovia para os veículos. Não é um estudo de capacidade, VDM ou circulação segura. Manuais desligados e limites mínimos de itinerários não são reativados.

Prévia e vídeo exibem ENSAIO CLÁSSICO; o 3D e os relatórios identificam modo ensaio. Não interpretar a presença dos veículos como aprovação de segurança ou conformidade normativa. Desmarcar retorna às proteções anteriormente configuradas, sem sobrescrever suas caixas individuais.

## Arrasto técnico sem vídeo

Clique em uma trajetória, escolha veículo, posição e extensão examinada e confirme Exibir arrasto. Verde indica que o corpo cabe na superfície; laranja indica amostras fora dela. Frente e traseira são representadas por um envelope rígido — não é simulação articulada de carreta. Havendo itinerário calculado no sentido selecionado, a inspeção usa seus pontos completos, incluindo a transição nos nós. Sem itinerário, o retorno identifica explicitamente um ensaio geométrico sobre o eixo.

A camada é um canvas de inspeção exclusivo do editor, limitado a aproximadamente 32 MB. Pan/zoom reutilizam o resultado, sem nova chamada de cálculo. Limpar arrasto remove apenas a inspeção. Nenhum desses desenhos integra a exportação do vídeo.

## Atualizar

Coloque o ZIP em atualizacoes/ e aplique pelo atualizador do aplicativo, aguardando o encerramento controlado. Projetos, vídeos e imagens persistentes continuam preservados. A revisão do código invalida resultados derivados antigos; confira a atualização dos fluxos antes de usar a inspeção.

Consulte evidencias/1.42.34 para validação executada e limites. A validação local não equivale à homologação nativa Windows/8 GB ou a uma certificação de segurança de tráfego.
