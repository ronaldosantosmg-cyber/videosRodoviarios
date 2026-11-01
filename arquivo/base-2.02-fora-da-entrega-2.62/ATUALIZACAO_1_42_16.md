# Rodovia Studio 1.42.16 — corrigir e liberar fluxos

O botão **Corrigir fluxos…** está na faixa abaixo dos menus. Também é possível digitar **CORRIGIRFLUXOS**. Os problemas aparecem primeiro, com motivo e ações:

1. **Localizar defeito**: ativa a visualização dos fluxos e centraliza o ponto informado.
2. **Recuperar partes válidas**: exclui os intervalos reprovados da circulação, revalida o restante e recalcula; não apaga o eixo DXF nem cria atalhos pelas partes excluídas.
3. **Recortar início/fim**: permite clicar nos dois limites do defeito no mesmo segmento. **Editar / reativar fluxo** abre as propriedades existentes.
4. **Revisar camadas que bloqueiam**: verificar camadas Barreira e Canteiro. Bordos e linhas de referência não devem ser classificados como obstáculos físicos.
5. **Revisar critério automático de canteiro**: permite suspender/restaurar explicitamente a inferência por proximidade de eixos. Isso não desliga barreiras, canteiros físicos, proibições manuais, colisões, sinais ou pare e siga.

O motor não bloqueia mais um eixo CAD nativo apenas porque outra linha perpendicular passou a ser o eixo mais próximo. Barreiras/canteiros físicos e proibições explícitas continuam sendo verificados. Barreiras abertas representadas por linhas também passam a integrar os obstáculos físicos (buffer geométrico de 0,20 m, além das margens existentes).

Em faixas derivadas automaticamente, o afastamento lateral é reduzido em tentativas limitadas quando isso melhora a acomodação do veículo na pista disponível. Não move o eixo original, não amplia o pavimento e não sobrepõe os dois sentidos ao centro. A trajetória ainda precisa passar pela validação final de corpo, direção e continuidade. Se a superfície não comportar o veículo, a circulação permanece bloqueada e exige corrigir a seção ou a classificação do pavimento.

Uma rota quebrada não ganha passagem por uma barreira só por solicitar recuperação. Após corrigir e recalcular, conferir o diagnóstico e a prévia. Desativações manuais não são removidas automaticamente.

Validação direcionada, autorizada pelo usuário: correções geométricas, interface, chamada real do motor, recorte, recuperação, preservação de DXF, semáforo, trem e pare e siga. DXF disponível usado como regressão, sem representar uma reprodução do projeto salvo atual do usuário. Não há certificação normativa, validação nativa Windows ou garantia universal de ausência de colisões. Fumaça e novo motor de pedestres permanecem fora desta correção.

Atualização: colocar este ZIP em atualizacoes/ e aplicar pelo próprio Rodovia Studio. Projetos, vídeos e cache persistente são preservados; snapshot e rollback continuam disponíveis.
