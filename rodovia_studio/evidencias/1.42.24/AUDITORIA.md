# Auditoria da revisão 1.42.24

Base: 1.42.23, commit 16e37e2f62fc84f4bed9161160215a49c1c4f3d8, branch desenvolvimento/rodovia-studio-1.42.

## Situação encontrada e alteração

- Existiam logs JSONL rotacionados, catálogo de uso, orientações por regras, inventário de camadas, perfis e classificação de materiais. Foram reutilizados; não foi instalado modelo neural nem serviço externo.
- O inventário conservava nomes, mas não contava tipos por camada. Foram acrescentadas contagens para distinguir linhas, contornos fechados e hachuras na assistência. O cache teve sua revisão incrementada.
- Perfis existentes tinham salvamento por nome. O novo editor acrescenta criação sem sobrescrita, proteção por revisão, importação/exportação tipada e prévia usando o mesmo comparador de padrões do motor. Regras referentes a outros desenhos são preservadas ao salvar um perfil aberto.
- O mapeamento de material de camada não alimentava a escolha de concreto/asfalto no pavimento. Agora alimenta esse caminho, preservando a prioridade das escolhas individuais por hachura.
- A assistência foi integrada aos menus Projeto/Ajuda e à aba Projeto. Não foi criado outro cálculo de tráfego ou motor gráfico.

## Dependências e controle

Logs → agrupamento/hipóteses/tempos → prompt JSON. Inventário DXF + configuração → proposta → revisão → confirmação → histórico/configuração → política de atualização existente. Materiais → classificação existente → geometria/superfície/3D/exportação. Perfis → biblioteca persistente; salvar perfil não altera a configuração nem dispara cálculo.

A aplicação verifica projeto, fonte, revisão da configuração e hash da prévia. Importação é somente dados, com sugestões desmarcadas. Não executa código, busca rede ou enfraquece barreiras/colisões/sinais/interdições. Classificação física não é uma autorização para remover uma barreira real; a revisão informa sua troca e exige substituição explícita.

Foram mantidos cálculo completo ao abrir/reabrir/salvar projeto/prévia/vídeo e modo Manual/Automático para confirmação de formulários. Não foram removidos componentes ou executadas limpezas de dados.

## Limites

A IA local é um sistema de regras, sem diagnóstico causal universal ou reconhecimento semântico autônomo. Considera registros retidos do projeto e caudas relevantes de error.log/ffmpeg.log; registros de outros programas e histórico já removido não são cobertos. Limite de 2.000 camadas, 500 regras por perfil e importação de 2 MiB. Fontes são vinculadas por tamanho/data de modificação; a revisão da configuração usa hash canônico. Arquivos externos não recebem hashes integrais nessa vinculação rápida.

O ensaio real usa o DXF DUPLICAÇÃO TH53 disponível, não o projeto salvo atual do usuário. Não houve ensaio nativo Windows/WebView2, OneDrive ou carga prolongada. O comparativo de abertura/pan/zoom da revisão anterior não foi repetido: esses caminhos não foram alterados, e não se afirma ganho percentual de desempenho nesta revisão.

## Complemento de interface solicitado durante a validação

Atualizar, modo de atualização e progresso foram movidos para a linha do SNAP/ORTO, preservando os IDs e os comandos. A duplicação de comando/coordenadas foi ocultada. X/Y permanecem visíveis; CRS, km, afastamento e observação de estaqueamento ficam no detalhe por hover/foco. Versão e estado de gravação ficam no detalhe da barra. As coordenadas são atualizadas em requestAnimationFrame durante o movimento; a rotina antiga aguardava o fim de uma pausa de 60 ms.

A rotina de sincronização lateral não deve mais retirar os parâmetros de dentro da expansão. Mais ferramentas expande horizontalmente com recolhimento no final. A aba Vídeo tinha uma expansão sem botões; recebeu atalhos para as implementações existentes de vídeos gerados, registros e prompt de reprodução. Parâmetros de apresentação recebeu dimensões próprias para botões, rótulos e seletores, evitando o estilo de botão de ícone estreito.

Duas expectativas antigas de test_v142_diagnostics falharam também no commit-base 1.42.23 (2 falhas/6 acertos reproduzidos em cópia isolada). Um trecho sem itinerário utilizável é vermelho, e arestas internas curtas podem existir para continuidade. As expectativas foram atualizadas: sem itinerário é impedimento; o teste visual compara frames antes/depois do diagnóstico, sem presumir exclusão de toda aresta interna. Os testes de seções/limites e barreiras permanecem. O teste de localização do progresso foi atualizado para o rodapé único solicitado.
