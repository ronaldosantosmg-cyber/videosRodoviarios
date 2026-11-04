# Rodovia Studio 3.17 — hachuras, materiais e janelas

Instale pelo atualizador e reinicie. O pacote atualiza o aplicativo existente sem substituir projetos ou DXF.

## Correções aplicadas

- Áreas de pista cadastradas manualmente usam o renderizador de materiais do editor: material explícito por área, material automático do projeto e parâmetros próprios de textura. A hachura diagonal deixa de cobrir o material no modo artístico com texturas ao vivo ligadas. No modo técnico ou com texturas desligadas ela continua como indicação de edição.
- Hachuras do DXF podem receber somente um material, mantendo o tipo “pela camada”. Antes, esse caminho apagava a escolha. Sem tipo reconhecido na camada, o material é conservado e é solicitada a definição do tipo, sem inventar uma classificação.
- Os vetores carregam o material e agrupam separadamente as superfícies com asfalto/concreto dentro de uma mesma camada e fase de implantação.
- Janelas de modelagem oferecem Aplicar por padrão. Paletas e diálogos permanecem sobrepostos por posicionamento fixo. Aplicar, cancelar, fechar e confirmação de alterações pendentes preservam suas funções.
- Ajuda das hachuras e texturas atualizada.

## Regras preservadas e limites

Alinhamentos secundários continuam locais conforme a 3.16. Sentidos individuais permanecem salvos. Não foram desligadas as verificações de pista, colisão, espaçamento, retenções ou saída no fim do itinerário. Não há retorno artificial ao início.

O nome de uma área não define seu tipo: “Pista nova 105 (OAE_EXISTENTE)” continua classificada como pista nova até corrigir explicitamente o cadastro. Uma área manual pode prevalecer sobre a hachura DXF subjacente. Não foram reclassificadas áreas automaticamente por nome, nem restauradas seções removidas pelo usuário.

A recusa geométrica do percurso Leste e a divergência preexistente do teste de setas citada na 3.16 permanecem pendências. Esta atualização não implementa dissolução visual progressiva por transparência nos extremos; mantém a saída física já existente e verificada, sem estacionamento terminal. Veja VALIDACAO_3_17.md.
