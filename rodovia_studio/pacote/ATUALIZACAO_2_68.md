# Rodovia Studio 2.68

Continua a 2.67 publicada nesta branch. Main preservada.

## Zebrados automáticos

Contornos fechados (polilinhas e hachuras, incluindo vazios) em camadas com palavra Zebrado/Zebrados/Zebra são lidos como canalização, mesmo com as demais camadas já mapeadas. Não se sobrescreve um papel escolhido explicitamente pelo operador. Camadas ocultas ou hachuras ignoradas ficam fora. Somente entidades realmente fechadas são candidatas; bordas abertas e fechamentos virtuais exigem conferência.

Na atualização, o programa consulta trajetórias habilitadas próximas e seus sentidos laterais. Com orientação não ambígua, sugere barras a +45° e cor branca para movimentos paralelos de mesmo sentido ou amarela para sentidos opostos. Cor explícita Branco/Amarelo no nome da camada prevalece na sugestão. A configuração manual sempre prevalece. Falta de fluxo, cruzamento do contorno, níveis diferentes ou movimentos divergentes deixam a área como Conferir sentidos. Essa pendência de pintura não bloqueia nem libera rotas de tráfego.

A sugestão não é certificação de sinalização viária. Aplicação, dimensões, cor e inclinação devem ser conferidas pelo responsável técnico no MBST volume IV. A consulta oficial continua indisponível na rede deste ambiente. Os valores iniciais permanecem ajustáveis (barra 0,45 m; centros 2,60 m).

## Uso

Cena → Mais ferramentas → Áreas e sinalização → Zebrados do DXF. Também há comando ZEBRADOSDXF.

- Configurar: nome, branco/amarelo, ângulo, largura e intervalo livre; Salvar e fechar ou Cancelar.
- Sentidos laterais: informar orientação das duas laterais (0° leste, 90° norte, 180° oeste); setas aparecem na amostra e na edição. Fluxo +45°/−45° usa os sentidos informados ou o fluxo próximo. A cor também pode ser sugerida pelos sentidos informados.
- As setas são referências para o zebrado; não alteram o sentido da via e não aparecem no vídeo.
- Localizar: enquadra a área. Mostrar pintura desmarcado desliga somente essa pintura e persiste após atualizar/reabrir.
- Usar contorno selecionado: aproveita uma área do desenho sem modificar o DXF. Comando ZEBRADOSELECIONADO.
- Desenhar contorno: clique os vértices e pressione Enter; configure as barras até esse limite.

Contornos vinculados têm identidade persistente. Configurar repetidamente a mesma área não cria cópias. Se a origem for removida/alterada, a configuração é preservada e indicada como Origem ausente; só pode ser reaproveitada como contorno manual por ação explícita. O reconhecimento automático está limitado a 200 contornos por atualização. Áreas com mais de 300 vértices por anel ou 30 vazios pedem um contorno de edição mais simples, sem truncar o DXF original. Pintura exige o modo de sinalização completa.

## Preservação e atualização

Vídeo, editor e 3D compartilham os parâmetros métricos; vazios das hachuras são preservados. As regras de tráfego e as trajetórias não são alteradas pela criação de pintura. O orçamento 3D considera superfícies, interferências e pintura em conjunto.

Feche o aplicativo e aplique pelo atualizador habitual. ZIP leve exige base 2.67 ou posterior; sem ela, use o completo. Preserve projetos, vídeos e imagens. Rollback permanece disponível. Não houve homologação Windows/Defender nem ensaio prolongado de uso intenso nesta revisão.
