# Entrega aprovada — Rodovia Studio 1.42.37

Pacote: `atualizacoes/RodoviaStudio_1_42_37_atualizacao.zip`.
SHA-256: `17801b1a59076d37c0bd956ce3de8dd73439cf02b98fe330a1d2d7cd4bd9adc6`.

## Mudanças entregues

- Aviso ENSAIO somente nos avisos/metadados, sem faixa nos quadros do vídeo.
- Imagem local + mapa: fallback para imagem local válida quando a rede falha, com aviso explícito; cancelamento e falhas reais continuam propagados.
- Prévia sem itinerário abre vista geral e diagnóstico para correção; exportação com veículos ativados e sem itinerário válido é recusada, preservando vídeo anterior.
- Leitura/gravação UTF-8 na assistência e nos workers; mensagens de ausência de eixo e leitura de KMZ melhoradas. Hachuras não são eixos.
- Reconhecimento de nomes de pavimento ampliado, preservando mapeamentos manuais. Respostas atrasadas do pincel são descartadas.
- Vista, prévia e sessões organizadas, confirmações dos formulários, legenda ligada ao estado real e rodapé mantido em uma linha. Ícone de seleção de nó corrigido.

## Validação desta revisão

961 casos aprovados, zero falhas, erros ou ignorados. A execução completa inicial e as repetições estão preservadas em `entrega-final/`, `entrega-aprovacao/` e `entrega-conferida/`. Foram corrigidos cenários antigos sem cadastro explícito de eixo, seletores da interface anterior e esperas que liam resultados ainda antigos. Nenhum caso obrigatório foi removido.

Na última etapa: 28 casos reexecutados e 933 resultados aprovados reutilizados, exclusivamente do mesmo produto. Hash do produto: `b5698e7330ea3a695701a16115368fba8ae7cc46acaf4acc2d7a00742a3441b8`. A retomada confere hashes dos testes, dependências e cobertura exata; mudança no produto exige nova suíte completa. Consulte os XMLs, `origem.json`, `retomada.json` e `evidencias_reutilizadas.json`. Não são testes de uma revisão anterior.

- MP4s reais com imagem combinada, mapa disponível/falha de rede simulada: H.264, 1280×720, 24 fps, 72 quadros decodificados em cada cenário, veículos visíveis nas amostras e sem aviso ENSAIO nos pixels.
- Exportação 3D com pessoas/fumaça conferida; o ensaio usa renderização por software, não representa desempenho de GPU Windows.
- Testes funcionais/visuais de edição, painéis, seções, densidade, segurança, cancelamento e atualização constam dos relatórios.
- Iniciador C# compilado com e sem WebView2; splash 1.42.37, fabricante e animação conferidos em Mono/Xvfb.
- Atualização pelo ZIP final e rollback 37 → 36 em instalação isolada, com espaço e acento no caminho: hashes de configuração, KMZ, cache GeoTIFF e vídeo anterior preservados. Evidência: `pacote-real.json`.
- Encerramento controlado e restauração após falhas também constam de `atualizacao-rollback.xml` (26 casos).

## Uso

Salve o trabalho e mantenha cópia do projeto. Coloque o ZIP em `atualizacoes/` da instalação e use a atualização do Rodovia Studio. Confirme o encerramento controlado e reabra pelo iniciador. Não extraia sobre o programa aberto. Para voltar, use o rollback; 36 e 37 compartilham schema 31.

Para veículos: Tráfego → Diagnosticar veículos; confira pavimentos/hachuras, cadastro/sentido dos eixos e seção antes de atualizar. O aplicativo não libera uma rota somente para apagar o aviso.

## Limites e prontidão

Nota estimada: **7,8/10** para uso intenso. Ainda faltam homologação nativa Windows/WebView2 em 8 GB, carga prolongada e reprodução com a configuração exata do projeto do usuário. O DXF disponível foi ensaiado com mapeamento conferido (7 itinerários); isso não comprova todas as rotas do projeto salvo. Não há promessa de conformidade normativa, reconstrução universal, desempenho superior ou qualidade Twinmotion. Não inclui pesos de IA 3B.

As durações dos testes estão nos logs; não são medições de antes/depois de pan/zoom ou de abertura em um PC Windows. Esses benchmarks continuam pendentes. Histórico de ZIPs preservado. Main deve permanecer em `4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3`; o trabalho é publicado somente em `desenvolvimento/rodovia-studio-1.42`.

## Histórico da tentativa anterior (não representa o estado desta entrega)

### Tentativa de entrega 1.42.37 — BLOQUEADA

Nenhum ZIP 1.42.37 foi gerado. Execução de validar_entrega.py interrompida após falhas na regressão histórica, sem aprovação de entrega. O log parcial não representa uma suíte concluída. Não houve ensaio final de atualização, splash ou rollback nesta tentativa. Os 41 testes dirigidos anteriores continuam documentados em formularios-etapa2, mas não equivalem à aprovação desta entrega.

Falhas reproduzidas: seletor de descarte ambíguo; percurso antigo de correção incompatível com a central atual; teste de textura esperando camada de hachura como eixo; refresh esperando sempre cache miss. É necessário revisar os contratos dos testes e conferir os demais erros do relatório antes de nova tentativa. Não foi suprimido teste para publicar o pacote.

Versões de manifesto restauradas para 1.42.36; código de interface continua na branch de desenvolvimento. Último ZIP disponível 1.42.36, SHA-256 9972064f53b66940f2d0b7ceb90375a361172775014cbdfe0cd4362c78bf4101. Download HTTPS conferido por HTTP 200 e hash integral. Esse ZIP não contém os ajustes de interface posteriores ao empacotamento anterior. Main preservada.
