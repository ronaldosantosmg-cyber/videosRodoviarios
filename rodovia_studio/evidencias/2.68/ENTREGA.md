# Rodovia Studio 2.68 — zebrados por contorno DXF

Base confirmada: revisão 2.67, commit b3dcd3e. Implementação exclusiva na branch desenvolvimento/rodovia-studio-2.68. Main preservada em 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3.

## Implementação

Reconhece contornos fechados em camadas com palavra Zebrado/Zebrados/Zebra, respeitando mapeamento manual, hachuras ignoradas e camadas ocultas. A coleção de pintura deixa de transformar esses contornos em preenchimentos sólidos. O fluxo viário existente fornece sentidos laterais e sugestão de inclinação/cor. Ausência de fluxo, movimento transversal, divergência, fechamento virtual ou geometria inadequada deixam a área como Conferir sentidos, sem bloquear o tráfego.

Central Zebrados do DXF em Cena, comando ZEBRADOSDXF. Configuração por área: cor, ângulo, barra, intervalo, ativação, sentidos laterais e setas de referência. Pode usar uma área selecionada ou desenhar contorno por vértices e Enter. A pintura é recortada dentro do contorno com seus vazios. Setas de referência só aparecem na edição/amostra, não no vídeo. Valores confirmados chegam à configuração e ao motor comum do editor, MP4 e 3D.

Vínculo estável por origem/forma evita cópias por atualização ou reedição. Origem ausente não apaga configurações nem reaplica pintura antiga silenciosamente. Manual prevalece sobre automático; desligamentos são preservados. Limite de 200 fontes por atualização e 300 vértices por anel editável, sem truncar o arquivo original. Projetos sem contornos candidatos não constroem o índice auxiliar de trajetórias. O orçamento do 3D soma superfícies, interferências e pintura.

## Testes desta entrega

final/resultado.json e pytest-resultados.xml: 123 testes aprovados, zero falhas/erros/ignorados. Gate total: 128.49 s, com três processos isolados. Não se compara esse tempo com tempo de uso do aplicativo.

Cobertura: HATCH com vazios, polilinha aberta, nomes/acentos/negações, mapeamento e ocultação, identidade independente da ordem dos vértices, duplicação de fontes, sentidos paralelos/opostos/ambíguos, configuração manual, desligamento, origem ausente, entradas inválidas, fechamento virtual, confirmação/cancelamento, contorno selecionado e direção zero com referências em lados distintos. Regressão de camadas, seções, tráfego, materiais, geometria e UI. Comparação das trajetórias antes/depois confirma que criar zebrado não muda a circulação.

MP4 produzido e decodificado com 72 quadros, 1280×720, 24 fps, além das exportações dos perfis existentes. Capturas final/268_zebrado_dxf.png e final/268_zebrado_sentidos.png inspecionadas. Splash e compilação C# em Mono/Xvfb aprovados.

A tentativa entrega/ também passou, mas foi substituída antes da publicação para corrigir a posição da seta com direção 0°. O pacote dessa tentativa foi arquivado localmente como rascunho não distribuído. Somente final/ aprova os ZIPs públicos.

pacotes-verificados.json registra aplicação dos ZIPs exatos a uma instalação isolada 2.67, verificação de hashes, rollback e preservação byte a byte de projeto, KMZ, GeoTIFF e vídeo. Versão leve recusa uma base inferior. publicacao.json registra os downloads HTTPS e SHA-256.

## Limites e uso

Sinalização completa precisa estar ativa para gerar pintura. Branco/amarelo e +45° são sugestões, com edição por responsável técnico; a aplicação e dimensões no MBST volume IV não foram certificadas. Portal oficial bloqueado pela política de rede. Não há certificação CONTRAN, homologação Windows/WebView2/Defender ou teste prolongado de carga. Arquivos privados do usuário não foram publicados.

Nota de prontidão: 7/10 para uso acompanhado, fundamentada nos testes funcionais/visuais e na atualização/rollback, com as limitações acima para uso intenso.

Feche o aplicativo, aplique pelo atualizador habitual e abra Cena → Mais ferramentas → Zebrados do DXF. Pacote leve exige 2.67 ou posterior; completo para outra base compatível. Preserve projetos, imagens e vídeos.
