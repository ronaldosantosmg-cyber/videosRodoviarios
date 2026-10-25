# 1.42.14 — painéis, assistente de correção e filtro de eixos

Revisão com validação direcionada, seguindo o fluxo simplificado solicitado. A suíte integral não foi repetida; não há promoção automática do canal estável. Código na branch de desenvolvimento, sem alteração de `main`.

## Painéis primeiro

A restauração do viewport após resize/regeneração chamava novamente as propriedades do fluxo, reabrindo o painel que acabara de fechar. Agora respeita o fechamento explícito, conserva o realce da seleção e permite reabertura manual.

Confirmações compartilham uma única solicitação. Descartar restaura o estado anterior e encerra a janela mesmo se uma atualização auxiliar de listas falhar. O fechamento recoloca os elementos na origem e libera os controles. Salvar e fechar também aplica texto de propriedades ainda não confirmado com Enter. Erros reais de validação/gravação mantêm a janela aberta com mensagem; não são tratados como gravação bem-sucedida.

## Orientação de fluxos

Em fluxos com problema, **Como corrigir este fluxo · assistente local** apresenta causa, instruções e justificativa. Ações permitidas: localizar ponto, abrir camadas e recalcular. O assistente não reativa sozinho fluxos desligados nem recomenda ignorar obstáculos ou reduzir o limite para liberar fragmentos.

É um **sistema especialista local de regras e diagnósticos geométricos**, não um modelo de linguagem treinado ou um sistema que aprende autonomamente. Não envia arquivos/coordenadas/logs para serviços externos. O modo de geração de prompt para IA permanece separado.

## Nós e pequenas rotas

Eixos com vértices consecutivos a menos de 5 cm podem receber simplificação derivada com tolerância de 2 cm; o DXF original é preservado e as verificações cinemáticas continuam. Identidades e desativações anteriores permanecem vinculadas, inclusive para eixos que já haviam sido unidos.

A seleção de eixos oculta rotas abaixo do limite atual imediatamente, comparando o comprimento sem arredondar. As escolhas de direção/desativação dos itens ocultos são conservadas. Rotas independentes curtas continuam excluídas da circulação; subtrechos internos de um eixo longo não são minirrotas independentes. Não há exclusão de originais ou projetos.

## Evidências

**36 testes direcionados aprovados**, sem falhas, erros ou ignorados, em 125 s. Cobrem fechamento após salvar/descartar, falha simulada de atualização visual, gravação sem Enter pela API real, permanência fechado após resize e reabertura manual, assistente/localização/camadas, limites exatos, escolhas ocultas, limpeza derivada, identidades, continuidade, recuperação e gravação rejeitada.

Capturas principais: `14214_01_painel_fechado_save.png`, `14214_01_painel_fechado_discard.png`, `14214_02_assistente_local.png`. Testes em Chromium real; alguns de interface usam o harness com dados determinísticos do motor.

DXF TH53 fornecido anteriormente: 31 eixos; 1.016 pequenos nós removidos na derivação; cinco itinerários produzidos, todos revalidados geometricamente; original preservado. Não é o projeto salvo atual do usuário, nem prova de correção de todos os seus bloqueios. SHA-256 do original: `7936e09e195212a85a894dbc48f5ad337f0cbe4f3195225e6f8137297e3e4538`.

Sintaxe Python/JavaScript, hashes e integridade do pacote verificados. Iniciador C# compilado com e sem WebView2 e splash conferido em Mono/Xvfb. Instalação sobre a 1.42.13, inicialização fora da raiz, encerramento controlado e rollback após mover a instalação aprovados; restauração dos arquivos anteriores byte a byte e preservação de sentinelas KMZ/GeoTIFF/vídeo. Assistente e módulo JS conferidos na instalação.

Prontidão para uso intenso: **7/10 provisória**. Não houve validação nativa Windows/OneDrive/WebView2, ensaio prolongado ou certificação normativa.

## Instalação e integridade

Copiar `RodoviaStudio_1_42_14_atualizacao.zip` para `atualizacoes/` e atualizar pelo aplicativo. Usar **Calcular e atualizar fluxos** para obter os novos diagnósticos.

- Tamanho: 4.101.307 bytes.
- SHA-256: `aa9cdf84f3380430ff2eae8c1139508720d5a106b0e162995e75865ae2098165`.
- Fonte validada: `5df70e9a8d5c8b4f541527605f2a18c739a144e54674a1107e757f78fa157659`.
