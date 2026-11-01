# Rodovia Studio 1.42.23

## Atualização automática ou manual

Ao lado de **Atualizar**, escolha **Manual** ou **Automático**. A preferência fica guardada neste navegador; sem preferência anterior, o modo inicial é Manual.

| Ação | Manual | Automático |
|---|---|---|
| Confirmar Salvar e fechar / Aplicar e salvar em um formulário | Persiste os valores e indica atualização pendente quando necessário | Persiste os valores e agenda uma atualização completa |
| Abrir ou reabrir projeto | Atualização completa | Atualização completa |
| Salvar projeto / Ctrl+S | Grava e atualiza completamente | Grava e atualiza completamente |
| Salvar como | Cria a cópia e atualiza a cópia | Cria a cópia e atualiza a cópia |
| Gerar prévia ou vídeo | Atualização completa antes da saída | Atualização completa antes da saída |
| Atualizar | Atualização completa da apresentação solicitada | Atualização completa da apresentação solicitada |

Projeto identificado ainda sem DXF/KMZ ou eixo permanece aberto e salvo; o programa pede os arquivos, em vez de iniciar um cálculo sem geometria.

A atualização completa refaz interpretação geométrica, superfície, faixas e simulação da apresentação solicitada. Fontes originais, imagens e cache GeoTIFF persistente são preservados. O reaproveitamento por eixo da revisão anterior continua disponível para cálculos parciais; as operações obrigatórias acima forçam o recálculo. Elas podem levar mais tempo em projetos grandes.

## Controle das tarefas

- Gravações internas usadas pelos cálculos continuam sendo somente persistência: não iniciam outro cálculo. Isso evita ciclos de salvar e recalcular.
- Confirmações próximas são agrupadas. Uma confirmação usada para iniciar o vídeo não agenda outra atualização redundante ao terminar a exportação.
- Recarregar resultados ao concluir uma tarefa não é tratado como reabrir projeto.
- Trocar para Manual retira uma atualização automática ainda aguardando início. Para interromper uma tarefa já iniciada, use **Cancelar** no rodapé.
- Um formulário aberto enquanto o cálculo está em andamento permanece em edição quando a tarefa termina.
- Se o cálculo falhar depois da gravação, o projeto continua salvo e o erro de atualização é informado separadamente.

## Vídeo e 3D

O vídeo 2D publica análise, editor e vetores da mesma geração calculada, além do MP4 validado. A exportação MP4 3D reconstrói a cena antes de capturar os quadros. Reconstrução preserva câmera, iluminação, tempo e diagnósticos; o acompanhamento é mantido quando o veículo correspondente ainda existe. Se a atualização 3D falhar, a vista anterior permanece disponível e a nova exportação não é iniciada.

## Instalar

Coloque o ZIP em `atualizacoes/` e use **Arquivo → Atualizar o Rodovia Studio**. Aguarde o encerramento controlado e reabra. Projetos, vídeos, DXF/KMZ, imagens originais e cache GeoTIFF são preservados.

## Validação e limites

118 testes dirigidos aprovados nesta revisão, com vídeos reais 2D e WebGL decodificados, modos automático/manual, Salvar/Salvar como, reabertura, cancelamento, recuperação e proteção de edições. Evidências em `suporte/documentacao/validacao_1_42_23/` e no repositório.

O DXF disponível foi exercitado em atualização completa e prévia neutra HD, com mosaico de 2048: 31 eixos, 6 fluxos revalidados, fonte preservada. Não é o projeto salvo atual do usuário. Não foi executada toda a suíte histórica nem validação nativa Windows/WebView2/OneDrive ou carga prolongada.

Prontidão provisória permanece **7,5/10**. Esta mudança atende à política de atualização solicitada; não constitui certificação de uso intenso. Main preservada.
