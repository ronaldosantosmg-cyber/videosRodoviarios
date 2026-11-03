# Rodovia Studio 3.12 — modelo artístico

Atualização do aplicativo existente, tomando a imagem fornecida como referência de acabamento. Não copia a geometria ilustrada nem cria barreiras, faixas, dimensões ou relevo sem dados do projeto.

## Como usar

Instale pelo atualizador e reinicie. Em **Aparência → Texturas**, escolha:

- **Artístico**: pavimento existente cinza-asfalto, grão fino e variação discreta; pintura sem desgaste automático; taludes com cobertura contínua e contorno discreto.
- **Realista**: agregado, remendos, fissuras e desgaste. Continua disponível como opção separada.

O projeto que já estava em Artístico passa a usar o novo acabamento quando a prévia/vídeo for recalculada. A opção Intensidade dos detalhes regula o microdetalhe e não troca o estilo. Ajustes de remendos/fissuras permanecem guardados para o realista.

O aterro mantém o verde-claro; o corte mantém o avermelhado com textura de grama. Na aparência natural/texturizada artística, os traços técnicos de offsets não cobrem o talude. O DXF e o perfil técnico preservam esses traços. Vazios, limites, cores manuais e pavimento rígido com juntas continuam respeitados.

A pintura mantém os traçados, cores e recortes do modelo; não converte linhas amarelas em brancas por semelhança com a imagem. Desgaste/transparência configurados manualmente continuam guardados. A alteração estética não é certificação normativa da sinalização.

## Integração

O mesmo seletor governa prévia de textura, editor Canvas, apresentação 2D, detalhe, vídeo e materiais da vista 3D. O cache de textura 3D distingue os estilos, permitindo alternar sem reutilizar o mapa anterior. A camada artística deixou de aplicar por baixo o desgaste da camada realista.

Sem alteração da rede ou dos parâmetros de tráfego. Resolução e FPS não foram reduzidos. Não se trata de reconstrução fotográfica 3D do empreendimento nem de garantia de tempo de renderização.

[Validação](VALIDACAO_3_12.md).
