# Evidências da 1.42.21

163 casos únicos aprovados, sem falhas ou ignorados no relatório consolidado. Os testes foram executados nesta revisão. A consolidação conserva o último resultado de cada caso; gate.log contém uma primeira execução cujo teste de navegação ainda procurava o botão no painel antigo. Esse teste foi ajustado para usar Tráfego → Corrigir problemas e reexecutado. Outros testes foram adaptados à separação entre topologia e velocidade e à tolerância de arredondamento de até 3/255 na composição de canvas. Não se reduziu a precisão das coordenadas.

Não foi executada toda a suíte histórica. Alguns testes históricos de interface ainda descrevem a organização anterior. O conjunto dirigido cobre contratos novos e regressões relevantes; não autoriza uma declaração de estabilidade universal.

## Medições

| Cenário | 1.42.20 | 1.42.21 |
|---|---:|---:|
| Área gráfica, 1366×900, DPI 1 | 644.280 px² | 744.639 px² (+15,6%) |
| Pan, 100 hachuras, DPI 1, mediana | 7,9 ms | 7,0 ms |
| Pan, mesmo cenário, DPI 2, mediana | 27,4 ms | 26,3 ms |
| Reconstruções fundo/técnico no ensaio DPI 1 | 46 / 48 | 2 / 3 |
| Memória lógica dos dois caches DPI 2 | 19,7 MiB | 22,7 MiB |
| Leitura inicial da geometria do DXF real | 17,32 s | 17,33 s |
| Geometria após alterar densidade, mesmo DXF | 17,62 s / nova leitura | 0,26 s / cache |
| Abertura da interface offline, mediana de 3 | 1,22 s | 1,27 s |
| Simulação sintética de 600 m / 30 s, uma amostra | 6,56 s / 25 veículos | 5,52 s / 25 veículos |

As medidas de geometria não representam o tempo da atualização completa nem da exportação. Na amostra de simulação, ambas as revisões tiveram zero colisões laterais/traseiras; isso não comprova segurança em qualquer projeto. A simulação não recebeu novo algoritmo nesta revisão; variação de tempo pode decorrer do ambiente.

A abertura ficou ligeiramente mais lenta no harness. A pintura estacionária DPI 1 passou de 0,8 a 0,9 ms; não se declara ganho para essa operação. Os caches ocupam mais memória porque a área desenhada aumentou, mantendo teto adicional de 32 MiB. Não se mediu RAM total/GPU. Pan em superfícies grandes conserva o caminho direto. Os números são de Chromium/Linux; não são certificação Windows.

## Testes dirigidos

- Cinco abas/oito menus, navegação, janela pequena, área gráfica, ajuda e materiais consolidados.
- Criar, salvar, reabrir, confirmar/descartar/fechar, histórico, desfazer/refazer e preservação da vista.
- Salvar sem POST de cálculo, pedidos equivalentes compartilhados, fila cancelável, descarte de contexto antigo e prévia válida sem nova tarefa.
- Densidade na configuração e na simulação real, topologia independente de velocidade, seções simples/duplicadas/terceira faixa e ativação por faixa.
- Barreiras, interdições, semáforos, pedestres, ferrovia e proteção entre veículos; fontes e desligamentos preservados.
- Cache de geometria válido/corrompido, fonte DXF preservada, materiais e comparação raster direto/cache.
- Imagem convertida persistente, modo misto após reabertura, fallback de detalhe e resposta atrasada de outra fonte recusada.
- Progresso único, etapa indeterminada, falha/cancelamento e exportação 3D cancelável sem sobrescrever vídeo anterior.
- MP4 2D com materiais: H.264, 1280×720, 24 fps, 72/72 quadros decodificados. WebGL real: exportação de 3 s, 1280×720, 24 fps, 72 quadros conferidos.
- DXF disponível: 31 eixos, 6 fluxos, 6 revalidados; SHA original preservado. Não é o projeto salvo atual do usuário.

pytest-direcionado.xml registra cada caso. medicoes.json contém números completos e limites. Os PNGs registram a inspeção visual. resultado.json registra as verificações do iniciador/splash via Mono e o hash da fonte; verificacao_pacote.json registra a aplicação do ZIP final, encerramento controlado, mudança de pasta, rollback e preservação dos dados.

## Prontidão

**7/10, provisória para uso intenso.** A revisão oferece evidência de funcionamento dirigido e reduz releituras/regenerações, mas faltam Windows/WebView2/OneDrive nativos e ensaio prolongado de grandes projetos. Incrementalidade ainda é por categoria, não por objeto em todas as operações. Reconhecimento semântico autônomo, reconstrução universal de rotas e núcleo CAD completo permanecem pendentes e fora deste pacote.
