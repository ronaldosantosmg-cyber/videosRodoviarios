# Rodovia Studio 1.42.3

## Comandos e área gráfica

Barra abaixo dos menus: Novo, Abrir, Salvar, Desfazer, Refazer, Propriedades,
Modificar, Pontos, Pan/selecionar, Zoom +/−, Enquadrar, Redesenhar e ações de
fluxos/prévia/vídeo. Modificar reúne as transformações; Pontos reúne grips,
inserção de vértice e pares DXF×imagem. Ferramentas oferece os grupos completos
do catálogo da 1.39 em cascata, sem espalhar todos os comandos na tela.
Mensagens, coordenadas e legenda continuam no rodapé. As rotas ficam em primeiro
plano quando a edição de fluxos está ativa; os diagnósticos técnicos não aparecem
no vídeo final.

## Movimento e diagnóstico

Ligações sem distância entre pontas não recebem mais curvas artificiais. Forçar
uma ligação não ignora interdições, proibições explícitas, canteiros nem inversões
do sentido declarado. A ligação recusada não vira uma nova entrada de veículos.
Os dados originais do projeto são preservados; o bloqueio afeta trajetórias
calculadas e a geração de veículos, com indicação de problema no editor.

Cada classe da frota tem comprimento, largura, entre-eixos e limite de
esterçamento equivalentes. A frente e a traseira são calculadas continuamente;
trajetórias com auto-interseções, cúspides, esterçamento excessivo, zigue-zagues
curtos ou corpo fora da pista são recusadas. Curvas reduzem a velocidade. A troca
de faixa precisa de espaço e geometria válidos e só avança com deslocamento do
veículo: um veículo parado não desliza lateralmente. O desenho conserva o tipo
real do veículo, sem transformar caminhões em carros para caber na curva.

Os limites são parâmetros conservadores da simulação, não valores legais:
carro 4,5 m/entre-eixos 2,7 m/35°; picape 5,3/3,1/35°; van 5,4/3,3/35°;
moto 2,1/1,4/35°; caminhão 12/6/32°; ônibus 12,4/6,2/32°;
carreta 18,6/8/30°. A carreta é representada por corpo rígido conservador;
não substitui análise de arraste de composição articulada.

**Depois de atualizar, abra o projeto e use Atualizar fluxos** para recalcular e
examinar os bloqueios. Confira os sentidos e as proibições do projeto antes de
exportar. A imagem enviada não contém os arquivos editáveis necessários para
validar aquele entroncamento específico. Não há certificação automática CONTRAN;
a conformidade depende também de sinalização, dados do projeto e revisão técnica.

## Atualização e preservação

ZIP exclusivamente em atualizacoes/. Mantidos atualização pelo aplicativo,
fechamento controlado, snapshot/rollback, caminhos relativos à instalação,
projetos/, videos/, KMZ e cache persistente de GeoTIFF. O gerador recusa dados
locais na raiz do pacote. Evidências e resultados acompanham a entrega em
suporte/documentacao/validacao_1_42_3/.

A validação inclui Chromium, vídeo MP4 decodificado integralmente, regressões,
compilação C# e splash animado com versão/fabricante via Mono/Xvfb. Execução
nativa em Windows/WebView2/PowerShell não foi realizada neste ambiente Linux.
