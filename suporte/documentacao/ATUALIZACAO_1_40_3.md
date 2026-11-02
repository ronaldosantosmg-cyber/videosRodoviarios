# Rodovia Studio 1.40.3 — Interação e Camadas

## Correções principais
- Ordem visual explícita para imagens locais sobrepostas: Topo, Subir, Descer e Fundo.
- A posição 1 é sempre a imagem de maior prioridade na sobreposição.
- Vista preservada durante regeneração, reload, abertura/fechamento de painéis e tela cheia.
- O ponto geográfico sob o cursor é preservado quando o viewport muda de tamanho.
- Seleção e seleção múltipla são restauradas após reload quando os objetos continuam existentes.
- Alt+clique percorre imediatamente os objetos sobrepostos.
- Tab, com o cursor sobre a área gráfica, percorre os objetos existentes naquele ponto.
- Clique repetido continua alternando objetos sobrepostos, preservando o comportamento CAD existente.
- Terminar operações de edição não limpa mais a seleção automaticamente; Esc/Desmarcar continuam limpando.

## Garantias
- Nenhuma alteração no motor de renderização de vídeo.
- Nenhuma alteração em projetos e vídeos durante atualização/rollback.
- Ordem das imagens é persistida na configuração do projeto.
- Compatível com o rollback seguro da 1.40.2.
