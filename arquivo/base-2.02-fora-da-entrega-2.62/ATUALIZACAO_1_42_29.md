# Rodovia Studio 1.42.29 — sondagem local de pesados

## Funcionamento

Em Vídeo → Veículos e fluxo, a opção **Sondar acostamento em conflitos de pesados (até 1 m)** permite o afastamento excepcional para a direita em encontros conflitantes e a verificação do arrasto nas curvas. Pode ser desligada e é salva por projeto. Não cria faixa de circulação nem altera a largura cadastrada do acostamento.

A referência é o bordo da superfície operacional de pista, obtida do pavimento ou da seção típica cadastrada. A área excepcional termina a no máximo 1 m desse bordo, exista ou não hachura de acostamento. Uma hachura de acostamento mais larga não aumenta esse limite. Sem superfície de pista identificada, a sondagem não inventa um corredor.

A trajetória local começa sem afastamento, aproxima-se suavemente da lateral e retorna à faixa. O motor confere corpo completo, varredura entre amostras, curvatura e folga entre veículos; volta a reservar o espaço em cada passo. Se não couber, conserva a redução/parada. Interdições, pedestres, semáforos, ferrovia, canteiros e barreiras não são desligados. Vazios internos não são preenchidos e não se presume suporte fora de tabuleiros de OAE.

A folga lateral passa a ser **0,30 m livres no total entre os corpos de dois veículos**: 0,15 m de reserva em cada um, sem exigir essa distância de linhas pintadas. O seguimento longitudinal mínimo continua em 2 m. Pisca direito indica o afastamento e esquerdo o retorno; as indicações de risco/parada existentes têm prioridade.

## Alcance e limites

Afastamento local para permitir passagem em encontros, não uma faixa contínua no acostamento. A ultrapassagem longitudinal pelo próprio pesado através do acostamento não foi acrescentada: a regra de seguimento e a mudança de faixa existentes permanecem ativas. A execução é compartilhada pela apresentação 2D, pelos veículos do 3D e pelo vídeo através da mesma simulação.

A frota existente foi preservada. Caminhões e ônibus usam os comprimentos já cadastrados e carreta usa 18,6 m; ainda é um corpo rígido conservador. Esta revisão não entrega dinâmica articulada nem homologa veículo de 30 m. O relatório informa as manobras aceitas/recusadas e o alcance da sondagem. Não é autorização normativa para trafegar no acostamento nem certificação CONTRAN.

## Atualizar

Coloque o ZIP em atualizacoes/ e aplique pelo atualizador do aplicativo. Abra o projeto, confira eixo e seção e gere uma nova prévia para recalcular a simulação com a revisão. Na janela de vídeo, confira a opção de sondagem. Não é necessário aumentar a densidade para ativá-la.

Preservados projetos, vídeos, DXF/KMZ, imagens originais, cache persistente GeoTIFF, snapshots e rollback. Nenhum ZIP histórico foi sobrescrito. A main permanece intacta.
