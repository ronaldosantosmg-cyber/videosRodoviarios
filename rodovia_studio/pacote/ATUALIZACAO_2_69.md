# Rodovia Studio 2.69 — TRIM visual

Pacote completo consolidado da base 2.68 publicada, com a revisão do TRIM. Main preservada.

## Como usar

Em Editar, use o ícone de tesoura TRIM. O botão ao lado abre as opções TRIM e Restaurar trechos. O menu superior Editar, o menu de botão direito e a barra de comandos executam a mesma função.

1. Digite TRIM (também APARAR ou OCULTARTRECHO), selecione a linha do DXF.
2. Clique no início do intervalo e depois no fim, ambos projetados na mesma linha selecionada. Aceita coordenadas pela barra de comandos.
3. Confira o trecho destacado e confirme Ocultar trecho e salvar. Cancelar/Esc antes da confirmação não modifica o projeto.
4. Use Desfazer/Refazer ou Editar → Restaurar trechos ocultos (comando RESTAURARTRECHOS) para recuperar o traço.

No botão direito, TRIM pode aproveitar a linha próxima do ponto clicado. Se outra operação estiver em andamento, conclua ou cancele antes. A linha selecionada aparece em azul, partes mantidas em verde e o intervalo ocultado em vermelho tracejado antes da confirmação. A indicação segue os vértices, inclusive nas curvas da polilinha.

## O que muda e o que é preservado

A ocultação é salva no projeto por origem da linha e distâncias a partir do primeiro vértice; não modifica o DXF. Afeta o traço no desenho técnico, a frente progressiva DXF, sobreposições, sinalização linear, bordos DXF e sua apresentação em vídeo/3D quando esses elementos são exibidos. Caches visuais são invalidados. No modo manual, a imagem raster anterior pode permanecer até Atualizar; a exportação usa a revisão atual conforme o fluxo de atualização existente.

É recorte visual, não remoção de eixo ou barreira de cálculo. Áreas preenchidas e máscaras de pavimento continuam válidas; ocultar o contorno não apaga a superfície. Não serve para liberar uma circulação impedida por obstáculo real. Trechos sobrepostos em outras camadas permanecem independentes.

Em contornos fechados, o intervalo segue a ordem dos vértices, sem atravessar a origem. Arcos/splines usam a polilinha convertida pelo leitor e sua tolerância existente; não se declara recorte analítico de um núcleo CAD. Seleção limitada a 50 mil pontos por linha, até 2 mil intervalos no projeto. Camadas congeladas não são selecionáveis; ocultas não participam da seleção. Fontes ausentes/alteradas geram aviso e conservam a configuração para revisão, sem aplicá-la a outra linha.

O modo antigo por interseções permanece disponível pelo comando avançado APARARINTERSECOES. O comando principal TRIM/APARAR passou ao fluxo solicitado, por dois limites escolhidos, sem depender de outras linhas de corte.

## Proteção e entrega

A seleção verifica o contexto do desenho antes de confirmar; resultados atrasados de outro projeto são descartados. Intervalos vazios, fora da linha e valores não finitos são recusados. Gravação rejeitada permite corrigir/tentar de novo, preservando o rascunho. Restauração também preserva estado em caso de falha de gravação.

Feche o aplicativo e aplique pelo atualizador habitual. Leve exige base 2.68 ou posterior; o pacote completo reúne a base anterior e esta revisão. Preserve projetos, imagens e vídeos. Atualização e rollback são verificados em instalação isolada; não é homologação nativa Windows/Defender.

## Linhas fantasmas: domínio e bordos

Hachuras classificadas como faixa de domínio ou bordo são interpretadas como traços originais separados, sem reparar/fechar esses traços como polígonos. Isso impede que um laço aberto ganhe uma diagonal de fechamento inexistente. Vários laços de uma hachura permanecem independentes. Tracejados de domínio e reamostragem de bordos conservam os vértices reais: não atalham curvas/cantos por segmentos ligando amostras distantes. A comparação de fechamento em coordenadas UTM usa tolerância absoluta, evitando o erro de tolerância relativa em coordenadas grandes.

O diagnóstico da sinalização informa se o bordo veio do DXF ou foi calculado a partir do contorno do pavimento. Não se apagam traços reais somente por serem longos. O usuário informou que o problema ocorre no TH57; o vídeo histórico está disponível, mas o DXF/configuração exatos do TH57 não foram localizados nesta sessão. A correção foi reproduzida com DXF sintético contendo hachuras abertas, laços separados e cantos; não se declara validação integral do TH57.

## Ícones fornecidos pelo usuário

148 SVGs do arquivo rodovia_studio_icon_pack.zip foram validados e incorporados como recursos locais. Menus, ferramentas e botões reconhecidos usam o novo catálogo; comandos sem equivalência mantêm o ícone anterior. A implementação não cria botões para funcionalidades ausentes, não muda atalhos/ações e mantém a ajuda existente. Identificadores de recorte SVG são únicos por instância; zebrados brancos/amarelos têm fundo de contraste. Os exemplos HTML/JavaScript/CSS do anexo não são executados. Origem e licença fornecidas estão preservadas em app/icons/rodovia/.

## Revisão indicada pelo usuário: DESAPROPRIAÇÃO e GE_HZ-HACOSTAMENTOPROJ

A sugestão por nome reconhece DESAPROPRIAÇÃO como domínio, mesmo que a hachura tenha um padrão típico de pavimento; GE_HZ-HACOSTAMENTOPROJ é reconhecido como acostamento. Não se sobrescreve uma classificação já escolhida: inconsistências aparecem nos avisos e na conferência abaixo.

Para projetos já salvos: Projeto → Conferir classificação e contornos (REVISARCONTORNOS). Confira as opções e use Salvar e atualizar. O comando pode mudar a correlação da camada/hachura para domínio e desativar cópias manuais de pavimento com nome de desapropriação, sem apagar seus pontos ou cadastros. Desativar uma área indevida muda a superfície operacional após a conferência; verifique o pavimento real cadastrado.

Por padrão, hachuras de pista/acostamento preenchem a superfície, mas não desenham automaticamente todo seu contorno como linha do CAD. Bordos calculados do pavimento também ficam desligados por padrão. Linhas CAD reais e bordos explicitamente classificados continuam desenhados. Para uma representação ilustrativa com esses contornos calculados, marque Mostrar contornos calculados das hachuras (ilustrativo). Não altera as barreiras físicas nem libera faixas de circulação.

O atalho genérico Tornar editável não transforma silenciosamente uma área de domínio em pista. Cadastros desativados permanecem na lista para recuperação, mas não desenham nem capturam a seleção na área gráfica. A validade de seleção TRIM considera as fontes e transformações, sem ser invalidada por câmera, densidade ou cadastros de superfície desativados que não alteram a linha.
