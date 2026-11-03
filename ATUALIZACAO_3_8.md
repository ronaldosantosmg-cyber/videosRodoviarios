# Rodovia Studio 3.8 — taludes e zebrados conforme o DXF

Atualização do aplicativo existente, mantendo as melhorias da 3.7 de tráfego, imagens, janelas sobrepostas, dia/noite e ajuda da versão.

## Taludes

Aterros passam a verde claro `#9cbd75`; cortes usam tom avermelhado `#b76954`. Ambos recebem textura de grama no editor, prévia, vídeo e 3D. Limites e furos continuam os do DXF. Cores e materiais explicitamente configurados pelo usuário permanecem respeitados.

O cadastro explícito de Corte/Aterro prevalece. Para entidades de talude genérico, a leitura considera nome tipificado e cor efetiva do DXF: verde identifica aterro, vermelho identifica corte. Respeita true color, ACI da entidade e BYLAYER, inclusive cor verdadeira da camada. A cor só tipifica entidades já identificadas como talude, sem transformar qualquer polígono verde em aterro. BYBLOCK sem cor herdada confirmada e cores ambíguas permanecem para conferência.

A proximidade de taludes tipificados só é apoio quando há evidência não ambígua e a distância amostrada é de até 30 m. As derivações registram a origem da classificação. A classificação agora ocorre antes da atribuição do material: o solo/pedra padrão do catálogo deixa de substituir automaticamente a grama. Nenhuma cor ou coordenada do arquivo DXF é regravada.

Depois de atualizar, use **Analisar arquivos** para refazer a classificação, confira os taludes e gere uma nova prévia. A ajuda e os seletores de cor foram alinhados à paleta nova.

## Rotatória e sinalização

As áreas zebradas fechadas do DXF controlam a apresentação: segmentos automáticos são recortados pela área completa, preservando bordos/linhas DXF, furos e linhas externas. A verificação usa interseção do segmento inteiro; o antigo teste pelo ponto médio podia perder uma linha longa que cruzava o zebrado.

Contornos internos dos zebrados são desenhados sem ligar um anel ao outro por uma corda. Os gores automáticos são recortados antes de gerar suas barras para impedir hachura dupla sobre a área DXF. PARE, faixas de pedestres e pinturas manuais são preservados. Polígonos virtuais/inválidos não são usados como autorização para apagar linhas. O traçado e os itinerários não são alterados por essa correção.

A marcação conforme MBST Volume IV §6.2 e a confirmação de orientação ambígua da 3.7 continuam. A correção não certifica um projeto normativo completo nem substitui a inspeção do DXF do empreendimento.

## Otimização medida

A grama de corte e aterro compartilha uma amostra de textura por quadro, em vez de repetir a mesma amostragem. Em nove repetições de uma etapa de sombreamento HD com ambos os tipos, a mediana passou de 40,364 para 37,055 ms (cerca de 8,2%). Os pixels permaneceram idênticos ao algoritmo anterior nessa comparação. Isso mede a etapa isolada, sem simulação, preparação da cena ou codificação. [Dados completos](proveniencia/medicoes-3.8.json).

A leitura evita construir árvores de proximidade quando não há taludes pendentes. O recorte de marcações usa STRtree para buscar somente áreas candidatas, evitando comparar todos os segmentos com todos os polígonos. Não se reduziu resolução, FPS ou qualidade do encoder.

Veja [validação e limites](VALIDACAO_3_8.md). O DXF específico da rotatória e o projeto completo do usuário não estavam disponíveis nesta revisão; os testes incluem arquivos DXF sintéticos com cores, furos e geometrias representativas.
