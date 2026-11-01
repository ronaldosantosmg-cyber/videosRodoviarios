# Rodovia Studio 1.42.22

Continuidade da 1.42.21, nas prioridades de tráfego, atualização parcial, interface e materiais/imagens. Motor gráfico e cálculos de segurança preservados.

## Tráfego e correção

- A recusa de uma ligação não torna vermelho um trecho que possui outra trajetória aprovada. O diagnóstico fica amarelo quando há circulação parcial validada, indicando as partes excluídas. Sem itinerário utilizável, o diagnóstico é vermelho. Isso não insere trajetórias nem suspende proteções.
- A central mostra **Localizar**, **Tentar correção automática** e **Editar manualmente**. Reconstrução, recuperação e recorte permanecem nas opções avançadas. A tentativa automática utiliza o reconstrutor conservador existente: continua limitada e pode ser recusada.
- Ações automáticas não reativam desligamentos manuais. Resultados antigos precisam ser atualizados antes de recortar ou solicitar recuperação.
- Intervalos sem seção cadastrada são listados com início/fim em metros. Edite os limites em **Montar seção típica**; lacunas não são preenchidas automaticamente.

## Atualização parcial

- Derivações de faixas são armazenadas por alinhamento em `_cache/route_lanes/`. Alterar a seção de um eixo invalida sua derivação, preservando a dos demais.
- Densidade não muda a geometria derivada; pare e siga associado ao eixo muda. Alterações de pontos, larguras, seções, configuração relevante ou algoritmo invalidam a entrada correspondente.
- O cache usa JSON comprimido, valida coordenadas/metadados e volta ao cálculo original se estiver corrompido. Possui teto de 64 MiB por projeto para seus próprios arquivos e recusa destinos por links simbólicos.
- A rede, os obstáculos, sentidos, interdições, semáforos e colisões continuam sendo avaliados. Não há atualização parcial por veículo ou por cada ligação nesta revisão.

## Interface

- Mantidas as cinco abas e o progresso único da 1.42.21.
- Testes históricos de ferramentas foram adaptados à navegação real pelas abas e opções avançadas. Acesso aos comandos da 1.39, destaque, ajuda, teclado, pan/zoom e desfazer foram reexercitados.
- A opção **Personalizado** dos materiais passa a efetivar sua escolha e preservar os demais ajustes, em vez de apenas mudar o texto da seleção.

## Materiais e imagens

- Material de uma área de pavimento DXF abre o editor de asfalto/concreto e amostra correspondente, em vez do formulário genérico de sobreposição.
- Materiais diferentes numa mesma camada são separados em malhas 3D; o último elemento não substitui o material de todos os demais.
- Áreas selecionadas do DXF preservam vazios internos existentes no modelo calculado e no vídeo. A seleção de áreas considera esses vazios.
- Materiais em modo automático acompanham o padrão do projeto também após reutilização de cache; escolhas manuais permanecem prioritárias.
- Ladrilhos de fontes web privadas são separados por projeto. Respostas antigas não redesenham outro projeto. Ao afastar o zoom, detalhes já carregados permanecem visíveis enquanto o novo nível chega.

## Atualização e limites

Coloque o ZIP em `atualizacoes/` e use **Arquivo → Atualizar o Rodovia Studio**. Depois de reabrir, use **Atualizar** para conferir o projeto na revisão nova. Projetos, vídeos, fontes e cache GeoTIFF persistente são preservados.

Validação dirigida desta revisão, com evidências no repositório e em `suporte/documentacao/validacao_1_42_22/`. Não equivale à execução de toda a suíte histórica nem à validação nativa Windows/WebView2/OneDrive.

Não foram implementados reconstrução universal de rotas, núcleo CAD completo ou reconhecimento semântico autônomo de imagens. Materiais continuam procedurais, sem promessa de equivalência ao Twinmotion. Edição completa de anéis internos por grips continua pendente; a proteção desta revisão preserva os vazios no modelo calculado.

Prontidão provisória: **7,5/10**. Houve melhorias dirigidas e testadas nos quatro pontos, mas faltam ensaio prolongado com projetos representativos, validação nativa e incremento mais fino da simulação para sustentar 9/10. Main preservada.
