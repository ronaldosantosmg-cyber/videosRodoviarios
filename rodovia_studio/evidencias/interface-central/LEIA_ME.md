# Menus, confirmações e central de correção — etapa de desenvolvimento

Base 1.42.36. Implementação na branch desenvolvimento/rodovia-studio-1.42, sem alterar main, versão, schema ou ZIPs históricos. Não é pacote instalável nem declaração de revisão final homologada.

## Mudanças

- Menu Editar sem segunda hierarquia de transformações/histórico. Seleção e propriedades continuam acessíveis; operações de arquivo permanecem em Arquivo.
- Menu Tráfego com Sentidos e nós, Testar circulação e Nós e edição de trechos. Inserir/selecionar/editar/mover/apagar nó, extremos, arrasto, recortar e juntar preservados. Criar ligação de ramal encaminha ao cadastro de nó existente com vínculos de origem.
- Corrigir problemas, comando CORRIGIRFLUXOS e orientação de correção abrem a mesma central de assistência existente, com proposta antes da aplicação. Ações avançadas preservadas em Recortar, juntar e recuperar. Não foi criado outro motor.
- Central explica os passos do especialista local; fluxo desligado manualmente não recebe proposta de liberação. Mantém regras físicas, validação de proposta/revisão, confirmação, revalidação e desfazer do serviço existente.
- Cabeçalho/rodapé fixos e conteúdo rolável, botão Fechar visível em 760×620. Proteção contra ações simultâneas e liberação dos controles após erro. Proposta já aplicada não pode ser reaplicada se falhar a leitura subsequente.
- Receber resultados ou restaurar o enquadramento após resize não abre Propriedades automaticamente nem descarta a seleção. Corrigido caminho que podia cobrir os comandos após recuperar um trecho.
- Diálogos de modelagem: Salvar e fechar / Salvar e atualizar explicitam o resultado. Cancelar conserva a escolha Salvar/Descartar/Continuar editando se houver rascunho. Contratos existentes dos painéis e perfis preservados.

## Uso

Tráfego → Central de correção dos fluxos (ou Corrigir problemas na faixa). Localizar ou Analisar e propor correção → conferir proposta → Confirmar e aplicar → Revalidar resultado. Para intervenção manual: Editar manualmente ou Recortar, juntar e recuperar. Reconstrução não garante resolver qualquer geometria e não suspende barreiras, canteiros, sinais ou interdições.

## Validação

Os XMLs desta pasta são execuções atuais. `testes.xml` cobre menus/central/confirmações e serviço real de correção; `testes-central-avancados.xml` cobre ferramentas preservadas, recuperação com fonte real sintética e falhas; `testes-confirmacao-final.xml` verifica salvar/fechar e prevenção de reaplicação; `testes-interface-definitiva.xml` repete a interface, a recuperação e os painéis após corrigir a abertura automática de Propriedades. Deduplicação por classname + nome em resultado.json, sem somar reruns como testes distintos.

Capturas de central e painéis: Chromium/Linux, projeto sintético isolado, sem inferência sobre Windows. A central compacta foi inspecionada visualmente. Sintaxe de todos os JS verificada usando o executor de validar_entrega.py; o gate histórico completo de empacotamento não foi executado.

As rodadas iniciais encontraram um erro na função simulada do teste , fixtures antigas com identificação posicional de eixo e acessos de testes a controles recolhidos. Corrigidos os testes para o contrato estável da 1.42.36; as falhas não foram ignoradas. O ensaio de ponta a ponta também revelou a abertura involuntária de Propriedades ao receber resultados; corrigida no produto e coberta por regressão de seleção/janelas. Testes legados da interface avançada passaram a abrir explicitamente essa interface, agora separada da entrada central.

Sem nova exportação MP4, teste de atualização/rollback ou validação nativa Windows nesta etapa. Nenhum novo pacote foi gerado. Prontidão global permanece na avaliação anterior de 7,8/10, sem ganho de nota atribuído só à reorganização.

## Pendências delimitadas

O registro único de todos os comandos, a migração de todos os formulários para um único contrato e a consolidação dos editores de seções/layers/materiais não integram esta etapa. Sentido, nós e reversão continuam nos contratos existentes. A correção automática continua condicionada à geometria e às proteções; nenhuma promessa de liberação universal ou conformidade normativa.

Resultado consolidado: **33 testes distintos aprovados**, sem falhas/erros/ignorados no resultado final de cada caso. A rodada definitiva de interface e ferramentas teve 24 aprovados; a recuperação real isolada teve 1 aprovado. As execuções intermediárias reprovadas constam nos relatórios e foram substituídas por reruns dos mesmos casos, sem contar repetições como testes adicionais. Sintaxe: 91 módulos JS aprovados.
