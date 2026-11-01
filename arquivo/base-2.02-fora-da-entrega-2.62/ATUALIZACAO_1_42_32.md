# Rodovia Studio 1.42.32 — confirmação das edições

## Corrigido

- Janelas de projeto, configuração/hachuras, materiais/apresentação e vídeo com rodapé acessível. Somente o conteúdo interno rola, mantendo as ações disponíveis inclusive em telas baixas.
- Rodapé com **Salvar e fechar**, **Descartar alterações** e **Cancelar**. Salvar confirma a configuração; descartar restaura o estado da abertura, preservando alterações que já existiam antes; cancelar/fechar com edição pendente permite salvar, descartar ou continuar.
- Gerenciador de camadas passa a usar o mesmo contrato de edição pendente. Visibilidade, congelamento e classificação podem ser conferidos na vista, mas a gravação do rascunho aguarda confirmação. Filtrar/marcar linhas não equivale a alterar o projeto.
- X, Esc e Cancelar do gerenciador usam o mesmo fechamento. Removida a duplicação do X legado que podia fechar por outro caminho.
- Falha de gravação mantém a janela e o rascunho, informa o erro e libera novamente os controles. Não é necessário descartar uma edição válida apenas para recuperar o uso da janela.
- Mantidos os identificadores e as ações de camadas existentes, sem duplicar o motor de cálculos. Não há alteração de geometria, tráfego, materiais, fumaça ou qualidade de renderização nesta revisão; o que muda é a confirmação e a apresentação dos campos existentes.

## Uso

Abra a janela ou uma de suas abas, edite e escolha **Salvar e fechar**. Use **Descartar alterações** para voltar ao estado de abertura. **Cancelar** ou X pedem uma decisão quando há alteração pendente. A atualização dos resultados continua respeitando o modo manual/automático já configurado; salvar um perfil reutilizável e aplicar esse perfil ao projeto continuam sendo ações distintas.

Não é preciso rolar até o fim de uma longa lista para encontrar os botões da edição. A rolagem ocorre no corpo da janela.

## Modo IA e pendências

Leia **MODO_IA_1_42_32.md**. O documento separa regras locais, diagnóstico de logs, correlação de camadas, ações assistidas, adaptador 3B e API online. Esta revisão não entrega pesos/runtime 3B nem uma IA autônoma nova. As respostas externas continuam sendo propostas estruturadas, sujeitas a validação e confirmação.

## Preservação e limites

Preservados projetos, vídeos, fontes DXF/KMZ, imagens originais e cache persistente GeoTIFF, além de histórico, snapshot, fechamento controlado e rollback. O pacote fica em atualizacoes/ sem sobrescrever os anteriores. A main não é alterada.

As verificações dirigidas de interface não substituem ensaio prolongado em Windows/WebView2 nem validação do projeto salvo do usuário. Não se promete correção universal de todos os diálogos, cálculos ou problemas de tráfego.
