# Validação da revisão 3.18

Validação em Linux/Python 3.12 e Chromium com dependências locais existentes. Não equivale a executar Windows/WebView2 ou todos os projetos do usuário.

## Evidências

- 69 testes dirigidos aprovados: confluências, admissão, mudanças de faixa, inicialização, espaçamento compartilhado, filas controladas, saídas, preservação de sentidos, materiais, sinalização, cache/checkpoints, apresentação parcial, dimensões, quarentena e preparação. Comando: `PYTHONPATH=suporte/sistema python -m pytest -q` com os 17 arquivos relacionados no histórico do commit.
- 16 testes adicionais aprovados: `test_v1425_scene3d.py`, `test_transition_anchors.py`, `test_v370_fleet_policy.py`, executados em `suporte/sistema` com `PYTHONPATH=.`.
- Testes de MP4: dois aprovados em `tests/test_video_pipeline.py`. Codificação real de 192 quadros com dois processos, leitura completa do MP4 e igualdade dos quadros entre cache frio/quente. Uma falha física injetada depois do primeiro bloco foi detectada antes de desenhar quadros; vídeo anterior e ausência de arquivo parcial conferidos.
- O teste de vídeo foi atualizado para exigir ausência de quadros antes de uma falha física: a validação completa agora antecede a codificação. Essa alteração corresponde ao comportamento solicitado, não à retirada do teste de preservação do arquivo anterior.
- Confluência sintética que reprovava no motor anterior: quatro sementes (1729, 1, 2, 3); 220 s para 1729 e 80 s para as demais. Zero colisões e zero violações, com intervenções de reserva e saídas efetivas verificadas.
- TH53 real disponível: DXF SHA-256 `5fd2fbecc4534f8e6e59aacd61b8b89b7d5a8d88af5778c82af8f45a84344f28`, configuração TH53 anterior mais recente. Leitura/rede e física de 220 s em aproximadamente 12,6 s neste ambiente; dois itinerários, 45 saídas, zero colisões e violações. Não é medição da renderização nem do computador do usuário. A configuração fornecida já não contém todas as seções antigas; o teste não recria seções ausentes por suposição.
- Canvas real: material local/automático, textura própria, vazios e dois materiais no mesmo layer conferidos com `scripts/verificar_materiais_areas.py`.
- WebGL real: `scripts/verificar_dissolucao_3d.py`; shaders compilados, opacidade por instância 1/0,5/0, recursos de geometria/material estáveis após 100 atualizações. Pool/sampler conferido por `scripts/pool_validar_3d.py`.
- Juntas orientadas e recortadas em polígonos com vazios; barreiras laterais sem fechar entradas; construção de OAE 3D e preservação dos bytes do DXF verificadas por regressão.
- Limpeza testada somente em pastas temporárias: restauração, retenção mínima, nomes iguais, proteção contra links e duplicatas por hash completo com referência preservada. Nenhuma limpeza executada na instalação do usuário.

## Limites e pendências explícitas

O último `config.json` enviado tem nome TH57, duração 180 s e coordenadas iniciais próximas de 704615/7812709. Os DXF e GeoJSON disponíveis do TH53 começam próximos de 734966/7830532, a dezenas de quilômetros. O log registra vídeo de 220 s. Não é correto combinar esses dados para afirmar que a falha exata aos 202,2 s foi resolvida no empreendimento TH57. É necessário o DXF e a configuração correspondentes àquela execução para essa reprodução específica.

A auditoria continua podendo reprovar um projeto com conflito real; não há promessa de ausência universal de erros. O espaçamento preventivo foi corrigido no motor e testado separadamente do recorte opcional. Operação parcial é identificada e não libera colisões físicas.

A auditoria dos pórticos aplica 12/18 m somente por comando explícito; não muda elementos por nome em qualquer projeto. Barreiras e materiais de apresentação não substituem dimensionamento executivo nem certificam conformidade normativa. Novas ancoragens continuam sujeitas à geometria/pavimento válidos.

A suíte histórica inteira não foi executada nesta revisão. Falhas históricas já identificadas no teste de setas `test_v14268_apresentacao_segue_km` e no fixture `test_v1423_motion` não são declaradas corrigidas. Não houve nova dependência nem consulta a outra IA externa nesta revisão.

A eliminação de quarentena acontece após 30 dias quando o aplicativo for aberto ou durante verificações periódicas; não existe serviço de limpeza com ele fechado.

## Interface e pacote

`scripts/verificar_janelas.py` aprovado em Chromium: quatro resoluções, nove painéis, ferramentas e linha de comando sem deslocar o Canvas; aplicar/descartar/cancelar e arrastar. Também confere a ordem Preparar/Gerar/Dia e noite, persistência de Noite e auditoria de travessias 12/18 m com apoios 12,9/18,9 m.

Portão com `--sem-suite`: sintaxe de 466 arquivos Python e 117 JavaScript, instalação sintética, importação, estrutura, reversão, componentes e servidor real aprovados. A suíte histórica integral é explicitamente pulada nesse portão; os testes dirigidos acima foram executados separadamente.

## Consulta de referências públicas

Consultados os textos oficiais mantidos no GitHub em 04/11/2026:

- [Eclipse SUMO — Safety](https://github.com/eclipse-sumo/sumo/blob/main/docs/web/docs/Simulation/Safety.md): distingue distância mínima física de intervalo desejado e reação; documenta riscos de inserção, mudança de faixa e confluências, e a necessidade de coerência entre reação e passo. Apoia manter controles independentes de admissão, avanço e auditoria. A regra de apresentação de 12 m/2 s é requisito deste aplicativo, não uma norma extraída do SUMO.
- [MDN — Using Web Workers](https://github.com/mdn/content/blob/main/files/en-us/web/api/web_workers_api/using_web_workers/index.md): cálculo em segundo plano sem interferir na interface. Neste aplicativo existente a física já é Python em tarefa separada; esta revisão preserva essa arquitetura em vez de criar um segundo simulador JavaScript.

As páginas diretas desses sites foram bloqueadas pelo proxy (403); as fontes oficiais no GitHub puderam ser consultadas. Nenhuma IA externa foi consultada.
