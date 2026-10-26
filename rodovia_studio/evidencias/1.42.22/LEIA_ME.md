# Evidências — 1.42.22

Base: 1.42.21, commit 9354edd7d78086f61a1deab9a871263a6d62bd1c, branch desenvolvimento/rodovia-studio-1.42. Main permanece no commit 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3.

## Alterações verificadas

| Prioridade | Entrega | Limite |
|---|---|---|
| Tráfego utilizável | Circulação parcial diferenciada de impedimento total, lacunas de seções localizadas por intervalo, central com três ações principais e avanço seguro para opções de recuperação | Reconstrutor continua conservador e limitado; não resolve qualquer ligação. Não preenche lacunas declaradas nem reativa desligamentos. |
| Atualização parcial | Derivação persistente por eixo; alterar uma seção recompõe aquele alinhamento, reutilizando os demais | Rede e segurança são reavaliadas. Não é simulação incremental por veículo nem atualização parcial de cada malha. |
| Interface consistente | Testes de ferramentas históricas adaptados às cinco abas, teclado, destaque, ajuda, opções avançadas, janelas e perfil Personalizado | A suíte histórica completa ainda não foi executada; validação nativa permanece pendente. |
| Materiais/imagens | Editor contextual correto para pavimento; materiais distintos por malha; modo automático coerente com cache; vazios preservados no cálculo; ladrilhos privados isolados por projeto e detalhe anterior no zoom | Texturas procedurais. Grips de anéis internos e equivalência visual com Twinmotion não foram implementados. |

Nenhum componente foi removido por busca estática. Rotas, workers, motores 2D/3D, atualizador e fontes persistentes foram preservados. O cache novo ocupa somente `_cache/route_lanes/`, valida JSON e coordenadas, limita seus próprios arquivos a 64 MiB e recusa links simbólicos. Se armazenamento/remoção do temporário falhar, a derivação válida continua; as falhas de cache aparecem em seus contadores. Isso não oculta falhas de materiais ou vídeo.

## Medição dirigida

Derivação de faixas de **12 eixos sintéticos de 5 km, 4 faixas por eixo**, sem testes concorrentes:

| Fase | 1.42.21 | 1.42.22 |
|---|---:|---:|
| Primeira derivação | 0,321 s; 12 eixos calculados | 0,459 s; 12 calculados |
| Repetição sem alteração | 0,458 s; 12 calculados | 0,205 s; 12 reutilizados |
| Alterar seção de um eixo | 0,313 s; 12 calculados | 0,153 s; 1 calculado, 11 reutilizados |

A primeira execução paga o custo de gravar o cache e ficou mais lenta nessa amostra. O benefício aparece na reutilização. Estes números não medem atualização completa, rede, simulação, MP4, Windows ou memória total e não demonstram ganho universal. Valores completos em medicoes.json.

## Validação

O relatório pytest-direcionado.xml consolida o último resultado de cada caso desta revisão; não reaproveita resultados de entregas anteriores. Foram exercitados:

- Circulação parcial com ligação rejeitada e impedimento real por falta de pavimento.
- Apenas o eixo alterado rederivado; densidade sem invalidar faixas; pare e siga invalidando a derivação correspondente; cache corrompido, destinos por symlink e falha de gravação/limpeza.
- Barreiras novas continuam impedindo passagem mesmo com faixas recuperadas do cache.
- Lacunas e limites coincidentes de seções; preservação de sentidos, desligamentos e limites mínimos, além das regressões de segurança.
- Comandos da 1.39 acessíveis na organização atual, teclas de navegação, ajuda, pan/zoom, seleção, desfazer/refazer e gravação sem cálculo automático.
- Criar, salvar e reabrir projeto; confirmar, descartar e fechar janela; orientação local e localização do defeito.
- Pavimento DXF no editor correto, perfis de materiais, malhas distintas no mesmo layer, materiais automáticos/manuais e vazios internos preservados.
- Imagem convertida persistente, modo misto e isolamento de respostas/ladrilhos entre projetos.
- Vídeos 2D e WebGL reais, ambos 1280×720, 24 fps, 3 s, 72 quadros conferidos; vídeo 2D H.264 com decodificação sem erros. Cancelamento não sobrescreve vídeo anterior.
- Atualização, falhas simuladas de troca, snapshot e rollback; o ensaio do ZIP final fica em verificacao_pacote.json no repositório.

O DXF disponível manteve seu SHA-256, 31 eixos e 6 fluxos revalidados. Não é o projeto salvo atual do usuário.

Os logs preservam as execuções. Falhas iniciais de testes que procuravam os controles na aba antiga foram corrigidas para navegar pelos botões reais, sem force-click. A consolidação só aceita casos cujo último resultado é aprovado, sem ignorados. É validação dirigida, não execução de toda a suíte histórica.

## Prontidão

**7,5/10, provisória.** Os quatro pontos receberam melhorias verificáveis; ainda faltam uso prolongado com projetos representativos, Windows/WebView2/OneDrive nativos e incremento mais fino da simulação para sustentar 9/10. Não há certificação normativa ou garantia universal de ausência de falhas.
