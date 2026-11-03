# Rodovia Studio 3.16 — alinhamentos secundários

Instale pelo atualizador e reinicie. Projetos e DXF não são substituídos pelo pacote.

Alinhamentos criados no editor passam a ser locais por padrão. Criar, editar, mover ou inverter um alinhamento secundário não substitui o eixo principal existente, sua referência de quilometragem, câmera ou orientação global do tráfego. Rotas secundárias continuam com suas escolhas próprias de circulação.

A substituição global exige a opção explícita **Usar como eixo principal do projeto** no comando Alinhamento. A opção inicia desmarcada. O novo campo `custom_axis.use_as_reference` tem padrão `false`, inclusive nos projetos antigos que não o contêm. A seleção do eixo CAD principal e a inversão geral explicitamente configurada permanecem vigentes. Sem eixo CAD reconhecido, o fallback de referência existente pode usar um alinhamento disponível; ele não substitui um principal já existente.

No TH53 fornecido, o alinhamento local de 1,03 km deixa de substituir a referência CAD de 10,22 km. O alinhamento local permanece salvo, selecionável e editável. Normal, invertido ou ausente, ele produz os mesmos sentidos e a mesma classificação dos eixos principais.

Esta revisão preserva as verificações de pista, colisão e regra de ouro. Não corrige por si só o percurso Leste recusado por corpo fora da pista, nem restaura seções de faixas removidas da configuração.

Veja VALIDACAO_3_16.md.
