# Validação dirigida — Studio 3.7

Executada em Linux, Python 3.12 e Chromium, em 03/11/2026. Atualização do aplicativo existente; nenhum aplicativo demonstrativo separado foi entregue.

- **110 testes passaram**, dois casos de relatório/API histórica foram desmarcados na seleção dirigida. Inclui MP4 dia e noite em 1280×720, 24 FPS, 3 s, 72 quadros decodificados integralmente; conservação dos veículos, inicialização sem aquecimento, aquecimentos fracionários, controles, guarda de colisões, admissão espacial, zebrados DXF com furos e exportação 3D.
- Pipeline real de imagens no Chromium: fila compartilhada de até seis cargas/decodificações, `decode` antes da publicação, fallback proxy/direto, repetição após falha, resposta 204, descarte de contexto antigo, cancelamento e cache LRU por pixels. Nenhuma biblioteca nova.
- Pool de amostras/objetos matemáticos do 3D: equivalência com interpolação anterior, buffers independentes atual/futuro, tamanhos variáveis e 100 atualizações sem novas instâncias de geometria/matemática no teste dirigido; limpeza ao fechar.
- Chromium com servidor real: editor obsoleto não solicitado automaticamente, atualização/3D respeitam tarefa em andamento e ausência de erros JavaScript.
- Nove painéis em quatro resoluções: área gráfica sem deslocamento; aplicar, descartar, cancelar e arrastar verificados.
- DIA/NOITE/ANOITECER persistidos; transição temporal e retorno no tempo no 3D; F1 com versão real e catálogo de comandos sem instruções ausentes.
- Sintaxe Python/JavaScript e servidor real/API/arquivos estáticos conferidos.
- Pacote com manifesto e hashes, instalação sintética, importação, reversão, componentes e inicialização real verificados pelo portão com `--sem-suite`. Esta opção não executa a suíte histórica completa.

## Medições

[Dados completos](proveniencia/medicoes-3.7.json), três repetições por cenário. Rede simples: três rotas paralelas de 4 km, densidade 8, velocidade 70 km/h. Tempos de **simulação**, sem renderização ou codificação:

| Duração do vídeo | 3.6, mediana | 3.7, mediana |
| --- | ---: | ---: |
| 3 s | 15,216 s | 0,228 s |
| 180 s | 49,226 s | 14,829 s |

O ganho inclui a mudança da população inicial: 282 → 93 veículos semeados; no vídeo de 180 s, 607 → 228 veículos admitidos no total. As contagens são determinísticas em cada versão; ambas geram 902 estados para esse cenário, sem colisões. O ambiente é compartilhado. Estes números não demonstram uma redução específica no projeto que levou mais de 40 minutos.

O perfil isolado de admissão com 1.240 veículos, mantendo as contagens, passou de 1,771 a 0,623 s sob cProfile. O perfil total passou de 8,325 a 7,143 s. São medições distintas do benchmark acima.

O teste de fila de 300 s foi corrigido depois de encontrar 71 violações na primeira proposta. Resultado final: [5,4,6] veículos por verde, zero colisões e zero violações. A demanda da fixture é 6 para manter fila real sem o aquecimento; a exigência de pelo menos quatro descargas foi preservada. A exceção acompanha a origem física da fila e sua dissolução limitada, sem permitir herança indefinida em trecho livre.

## Limites conhecidos

A suíte histórica inteira não foi certificada. Uma verificação adicional do antigo `test_v113::test_night_darkens_scene_and_lights_signage_and_vehicles`, já listado em `linha_base_falhas.txt`, ainda falha porque a amostra de pintura fica vazia na fixture antiga; não foi contada como aprovação. MP4 dia/noite e transição 3D foram validados por testes atuais independentes.

As divergências históricas de quantidade de fases de pare/siga e ocorrência de ultrapassagem continuam exigindo cenários atualizados/reprodução; as verificações de colisão desses cenários passaram. Consulte também [as pendências anteriores](PENDENCIAS_3_6.md). A consulta ao GitHub em 03/11/2026 não encontrou issues abertas; isso não elimina as pendências registradas nos arquivos.

O empreendimento completo, o computador do usuário, GPU física e Windows/WebView2 não foram executados neste ambiente. A automação Windows do repositório oferece verificação adicional em cada publicação. A grade espacial filtra candidatos; os testes geométricos continuam necessários e o custo não é constante em concentração arbitrária de veículos.
