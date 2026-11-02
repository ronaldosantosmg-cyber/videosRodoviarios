> **Atualização 1.39: 315 testes passaram** (311 da 1.38 + 4 novos: bordas 255/0 ligadas à beira, opção anterior e manter, 16 bits e migração, tráfego sem ziguezague por trecho curto). Teste do padrão das bordas da 1.17 ajustado ao novo padrão. Regressão TH57 idêntica à 1.38; itinerários do TH57 iguais. Detalhes em ATUALIZACAO_1_39.md.

> **Atualização 1.38: 311 testes passaram** (306 da 1.37 + 5 novos do instalador do leitor ECW: só pacotes prontos, queda para download direto após a falha de compilação, mensagem sem rede, proxy do Windows, endereço pela versão do Python). Regressão TH57 idêntica à 1.37. Detalhes em ATUALIZACAO_1_38.md.

> **Atualização 1.37: 306 testes passaram** (301 da 1.36 + 5 novos: conversão de DWG com conversor de teste, API de DWG, esquema 29 e frota, vegetação e pedestres no vídeo e um teste de tela). Teste de congestionamento da 1.12 fixado na frota clássica (e verificação extra com a variada). Regressão TH57 idêntica à 1.36. Detalhes em ATUALIZACAO_1_37.md.

> **Atualização 1.36: 301 testes passaram** (294 da 1.35 + 7 novos: sol e sombras, padrão idêntico, clima, sombra pelo sol, antes/depois, câmera por pontos-chave e um teste de tela). Regressão TH57 idêntica à 1.35. Detalhes em ATUALIZACAO_1_36.md.

> **Atualização 1.35: 294 testes passaram** (285 da 1.34 + 9 novos: tipos de obra e km no texto, modelo Excel ida e volta, CSV, cronograma MS Project XML, situação por data, esquema 28 e categorias, vídeo com obras e linha do tempo, API de obras e um teste de tela no Chromium a 150 % com propriedades, seleção, menu, ferramentas, importação e obra no desenho). Dois testes da 1.34 ajustados (esquema ≥27; painéis contados e achados pelo campo). Regressão TH57 idêntica à 1.34. Detalhes em ATUALIZACAO_1_35.md.

> **Atualização 1.34: 285 testes passaram** (279 da 1.33 + 6 novos: esquema 27 e migração das texturas, texturas artístico-realistas, amostra de textura, tela sem TH57/versões, módulos 39–42 e temas, e um teste de tela no Chromium com painéis, temas, progresso, download, comandos contínuos e arraste). Testes de tela anteriores passaram a abrir na “Coluna clássica”; dois testes pressionam Enter duas vezes (a ferramenta continua após o primeiro). Regressão TH57 (projetos existentes) idêntica à 1.33. Detalhes em ATUALIZACAO_1_34.md.

> **Atualização 1.33: 279 testes passaram** (274 da 1.32 + 5 novos: tempos em Python e JS, tempos nas mensagens do servidor, estrutura da tela e um teste de tela no Chromium com abas, recolher, reabrir ao selecionar, janela flutuante, área máxima, rodapé da tarefa e faixa de opções). O teste de tela da 1.26 passou a abrir os registros pelo comando LOG (o botão saiu da coluna e foi para os menus). Regressão TH57 idêntica à 1.32. Detalhes em ATUALIZACAO_1_33.md.

> **Atualização 1.32: 274 testes passaram** (263 da 1.31 + 11 novos: reorganização 1.31→1.32 com .exe antigo e entrega pelo atualizador 1.31 real, raiz arrumada, arquivo de vídeos, geração sem substituir, API de vídeos/pastas/limpeza, categorias de limpeza, qualidade — migração, codificador, nitidez, nível 20 e superamostragem — e um teste de tela). Testes do atualizador (organização), do iniciador (versão) e de esquema ajustados. Regressão TH57 em Padrão idêntica à 1.31. Detalhes em ATUALIZACAO_1_32.md.

> **Atualização 1.31: 263 testes passaram** (257 da 1.30 + 6 novos de estrutura: módulos da interface e script montado, nomes globais repetidos e extensões válidas, ESLint, nomes indefinidos no Python e rotas da 1.30, CSS externo com variáveis, registros na tela). test_v17_speed ajustado ao novo lugar das rotas. Regressão TH57 idêntica à 1.30; capturas de tela iguais às da 1.30. Detalhes em ATUALIZACAO_1_31.md.

> **Atualização 1.30: 257 testes passaram** (252 da 1.29 + 5 novos: geometria das faixas das rotas, rotas na rede de tráfego sem pintura a mais, projetos/renomear/miniatura/modelos pela API, esquema 25 e um teste de tela no Chromium com abrir projeto, modelos, rota com trecho duplo, grupos recolhíveis, gerenciador de camadas e pincel). Teste de tela da 1.29 passou a esperar o projeto abrir (falhava às vezes por pressa). Regressão TH57 idêntica à 1.29. Detalhes em ATUALIZACAO_1_30.md.

> **Atualização 1.29: 252 testes passaram** (246 da 1.28 + 6 novos: opções por tipo, nomes, envio de DXF+KML e retirada, região de textura, aparência da sinalização e um teste de tela no Chromium). Testes de tela anteriores ajustados ao novo layout (faixa de opções, caixas de diálogo próprias para nomes). Regressão TH57 idêntica à 1.28. Detalhes em ATUALIZACAO_1_29.md.

> **Atualização 1.28: 246 testes passaram** (245 da 1.27 + 1 novo no Chromium: comando pelo menu termina limpando a seleção, menu fecha, edição durante a análise não se perde, prévia refeita sozinha). Detalhes em ATUALIZACAO_1_28.md.

> **Atualização 1.27: 245 testes passaram** (236 da 1.26 + 9 novos: fluxos — curvas, ligações, velocidade; textura própria por área; área do desenho; velocidade de avanço; iniciador WebView2 (código); teste de tela no Chromium da edição direta, menu da seleção, textura, caixa de chamada, ligações, avanço e Sobre). Regressão TH57 idêntica à 1.26. Iniciador 1.1 não compilado aqui. Detalhes em ATUALIZACAO_1_27.md.

> **Atualização 1.26: 236 testes passaram** (228 da 1.25 + 8 novos: pórticos e chamadas no quadro, ocultar/congelar camada, hachuras, seleção de linha, imagens/sessões/registros pela API e um teste de tela no Chromium). Regressão TH57: padrão idêntico à 1.25; motor “anterior” idêntico à 1.23. Detalhes em ATUALIZACAO_1_26.md.

> **Atualização 1.25: 228 testes passaram** (222 da 1.24 + 6 novos: quadkey e WMS 1.1.1, busca no catálogo QuickMapServices pela área do trecho com cache, conversões e recusas, amostra de nitidez, API buscar/testar/usar e painel no Chromium). Catálogo e ladrilhos simulados; acesso real não testado neste ambiente. Detalhes em ATUALIZACAO_1_25.md.

> **Atualização 1.24: 222 testes passaram** (210 da 1.23 + 12 novos: leitor ECW interno com GDAL simulado, texturas editáveis, leitura de hachuras, snap exato, motor de montagem, editor completo no Chromium). Motor “anterior” idêntico pixel a pixel à 1.23 no TH57. ECW real e Windows não testados. Detalhes em ATUALIZACAO_1_24.md.

> **Atualização 1.23: 210 testes passaram** (206 da 1.22 + 4 novos: código do iniciador em C# 5 e compilador do Windows, preparo sem abrir o aplicativo, porta informada ao .exe e reaproveitamento de instância aberta, campos obrigatórios vazios recusados no editor). O Rodovia Studio.exe não foi compilado neste ambiente (sem compilador do Windows). Detalhes em ATUALIZACAO_1_23.md.

> **Atualização 1.22 (inclui 1.21): 206 testes passaram** (196 da 1.20 + 7 da 1.21: material pelo nome da camada/padrão/área, juntas a cada 5 m e tom por placa, concreto no mosaico e nos ladrilhos, contraste projeto × imagem, hachura técnica limpa e migração, representação escolhida e editor; + 3 da 1.22: alinhamento por cliques, salvar como e edição tipo CAD no navegador). Testes de esquema das versões 1.20 e 1.21 passaram a aceitar versões mais novas. Com a configuração padrão, idêntico ao pacote 1.20 no TH57. Detalhes em ATUALIZACAO_1_21.md e ATUALIZACAO_1_22.md.

> **Atualização 1.20: 196 testes passaram** (183 da 1.19 + 13 novos: trajetória sem recuos e sem zigue-zague, curva fechada dentro da pista, rede sem recuos, sentido pelo eixo em pista dupla, área de pista prevalecendo sobre o DXF, acostamento por início/fim/largura, exportação/importação, hachura ancorada nas coordenadas, perfil técnico com voo contínuo e indicador de progresso, conferência DXF×KMZ, blocos vazios, conferência do MP4 e editor no navegador). Dois testes da 1.19 passaram a aceitar esquema 18 ou mais novo. Com “Como na 1.19” nas duas opções novas, idêntico à 1.19 no TH57. Detalhes em ATUALIZACAO_1_20.md.

> **Atualização 1.19: 183 testes passaram** (172 da 1.18 + 11 novos: ajuste da imagem local por deslocamento/rotação/escala, chave de cache inalterada sem ajuste, API de prioridade e ajuste, fontes web Wayback/XYZ/WMS e cache, lista da Wayback sem internet, mosaico por ladrilhos georreferenciado, chave do detalhe, limpar trabalho/desfazer/lixeira, esquema v18, caminho longo do atualizador e editor no navegador com Enter, mover, grips, ícones e recorte da prévia). O teste do vão da passarela da 1.18 passou a arrastar a ponta (o centro agora move a passarela). Padrão idêntico ao pacote 1.18 no TH57. Detalhes em ATUALIZACAO_1_19.md.

> **Atualização 1.18: 172 testes passaram** (165 da 1.17 + 7 novos: setas sem excesso, camada 0 separada por cor/tipo com avisos, migração preservando camadas, acesso com tapers e fluxos, exportação do acesso, editor com km/vão/acesso, faixas por sentido com acostamento e 3ª faixa). Com as opções de compatibilidade, idêntico à 1.17 no TH57. Detalhes em ATUALIZACAO_1_18.md.

> **Atualização 1.17: 165 testes passaram** (157 da 1.16 + 8 novos: leitura por blocos e visões reduzidas, mosaico com prioridade e bordas sem dados, JPEG2000 com arquivo de mundo e GeoJP2, camada de detalhe com imagem local, mosaico base de várias imagens, API de ladrilhos/informações/conversão ECW simulada, editor no navegador e esquema v16). Dois testes da 1.11 passaram a indicar que o fundo é Esri. Padrão idêntico à 1.16 no TH57. Detalhes em ATUALIZACAO_1_17.md.

> **Atualização 1.16: 157 testes passaram** (151 da 1.15 + 6 novos: texturas só nas superfícies, trilhas de roda na pista existente, taludes com aparência de terreno, ajuste de cor da imagem detalhada, detalhe a 0,1 m e esquema v15). Texturas “Anteriores” idênticas à 1.15 no TH57. Detalhes em ATUALIZACAO_1_16.md.

> **Atualização 1.15: 151 testes passaram** (142 da 1.14 + 9 novos: faixas pela largura e por trecho, retenção/PARE no T, setas por itinerário e por faixa, faixa de pedestre/zebrado/placas e área sem sinalização, desenho no quadro de dia e de noite, sinalização do DXF, esquema v14 e exportação, gore na bifurcação, ferramentas do editor no navegador). Os testes da 1.10 sobre a sinalização limpa passaram a rodar no modo Básico. Modo Básico idêntico à 1.14 no TH57. Detalhes em ATUALIZACAO_1_15.md.

> **Atualização 1.14: 142 testes passaram** (135 da 1.13 + 7 novos: perfil padrão x TH57, curingas/perfis do usuário, migração da pista existente, modelo com camadas de nomes arbitrários, cores por tipo, API de perfis/prévia por camada e editor com seta girável). TH57 idêntico à 1.13. Detalhes em ATUALIZACAO_1_14.md.

> **Atualização 1.13: 135 testes passaram** (131 da 1.12 + 4 novos: transição dia/noite, cena noturna com sinalização e lanternas, esquema v12 e duas janelas sincronizadas no navegador). Detalhes em ATUALIZACAO_1_13.md.

> **Atualização 1.12: 131 testes passaram** (118 da 1.11 + 13 novos: bordos pelo contorno, eixos fora das junções, setas em todas as faixas, mão de direção na ilha, simulação sem colisão em densidades 1 e 5, engarrafamento, interdição parcial e total, regras do canteiro, desenho das interdições, modelo anterior, esquema v11/exportação e editor no navegador). TH57: 0 colisões traseiras. Detalhes em ATUALIZACAO_1_12.md.

> **Atualização 1.11: 118 testes passaram** (107 da 1.10 + 11 novos: texturas em alta resolução, transição base/detalhe, georreferenciamento da imagem detalhada com ladrilhos simulados, desistência rápida sem internet, cena para processos auxiliares, OAE por vértices com sentido e exportação, fluxos e sinalização na análise, esquema v10 e editor no navegador). Com o detalhe desligado, os quadros TH57 de 14, 40 e 96 s são idênticos aos da 1.10. Imagem Esri nível 19 não baixada neste ambiente. Detalhes em ATUALIZACAO_1_11.md.

> **Atualização 1.10: 107 testes passaram** (93 da 1.9 + 14 novos: pintura limpa sem cruzamentos, modos de setas, áreas sem sinalização, migração v9, marcos/seta/cidades/grama desenhados, cidades OSM com cache e sem internet, exportação/reimportação, entradas degeneradas e editor no navegador). Com as opções “Anterior” e anotações desligadas, os quadros TH57 de 14, 40 e 96 s são idênticos aos da 1.9. Detalhes em ATUALIZACAO_1_10.md.

> **Atualização 1.9: 93 testes passaram** (86 da 1.8 + 7 novos: conversão CRS ↔ Web Mercator, cache e validação de ladrilhos, vetores da análise, ajuste DXF sem prévia e editor no navegador sobre a imagem web). Ladrilhos reais da Esri não puderam ser baixados neste ambiente (testes com ladrilhos simulados). Os arquivos do motor de vídeo não mudaram. Detalhes em ATUALIZACAO_1_9.md.

> **Atualização 1.8: 86 testes passaram** (76 da 1.7 + 10 novos: estaqueamento, destaques, ajuda e atualizador). Scripts .cmd/.ps1 do Windows não executados aqui. Detalhes em ATUALIZACAO_1_8.md.

> **Atualização 1.7: 76 testes passaram** (62 da 1.6 + 14 novos: elevação, processos paralelos, perfil rápido e ficha técnica; o teste de interface inclui a tela cheia). Detalhes em ATUALIZACAO_1_7.md.

> **Atualização 1.6 (fases A–D): 62 testes passaram** (21 anteriores + 41 novos: 15 da fase A, 12 da B, 7 da C, 6 da D e 1 de interface no navegador). Ambiente: Linux, Python 3.13, shapely/pyproj compilados no ambiente. Regressão TH57: o modo Anterior gera quadros idênticos à 1.2. Medições e limites em ATUALIZACAO_1_3.md a ATUALIZACAO_1_6.md. O iniciador e o atualizador do Windows não foram executados aqui.

> Atualização 1.1: 10 testes passaram; medição e limitações em ATUALIZACAO_1_1.md. O relatório abaixo registra a validação original 1.0.

# Testes executados — Rodovia Studio 1.0

Ambiente de execução: Linux, Python 3.12. Dependências fixadas em requirements.txt. O iniciador PowerShell/CMD foi preparado para Windows x64, mas não foi executado em Windows neste ambiente.

## Testes automatizados

**7 testes passaram.** Incluem:

- Validação de parâmetros, quilômetros, duração e polígonos incompletos.
- Leitura de geometria DXF e subdivisão de curvas.
- Conversão de KMZ para CRS projetado e rejeição de CRS geográfico para o motor.
- Geração real de MP4: 1280×720, 30 fps, 90 quadros.
- Fluxo completo da API: criar projeto, upload, análise em processo separado, prévia, confirmação de coordenadas, renderização, download e cancelamento.
- Rejeição de extensões não suportadas, KMZ inválido e origem externa nas operações de escrita.
- Área de exclusão e bloqueio de veículos nessa região; desenho de intervenção.
- Rejeição de coordenadas NaN.

Foi verificado adicionalmente um DXF com eixo LINE de apenas dois pontos: comprimento calculado de 100 m, sem erro de leitura.

## TH57 real

O desenho ANTEPROJETO TH57.dxf e o mosaico em cache foram utilizados pelo motor para gerar uma prévia e um vídeo novo de **6 segundos, 2560×1440, 30 fps, 180 quadros**. A exportação H.264 terminou com sucesso. A amostra é incluída em conferencia/amostra_motor_TH57.mp4, recodificada para distribuição com o limite de 18 Mbit/s adotado pelo aplicativo.

Esse teste comprova o funcionamento do motor com o arquivo real em 1440p. A renderização nova completa de 202 segundos não foi executada nesta validação; a configuração de 202 segundos e o cálculo de 6060 quadros estão disponíveis no aplicativo.

## Referência idêntica

A exportação da referência pela API foi executada e comparada com o vídeo aprovado incluído. Os hashes SHA-256 são iguais:

`1d8cc8267015132a80ec4363bb1e5a66f39361d2a7e897ba509c7974f97e488b`

Arquivo: 456.658.115 bytes; 2560×1440, 30 fps, 6060 quadros, 202 segundos. Essa operação copia o vídeo aprovado sem modificações; ela não recompõe a cena a partir do DXF.

## Windows e interface

- Os 12 pacotes principais fixados foram encontrados e baixados em versões compatíveis com Windows x64 / Python 3.12, quando aplicável com wheels binários.
- A disponibilidade desses pacotes não equivale à execução do aplicativo em Windows. O preparo completo depende também das dependências transitivas e do acesso à internet no computador de destino.
- Sintaxe JavaScript da interface verificada com Node.js.
- Código Python compilado sem erros.
- Diagnóstico do FFmpeg executado com codificação real em libx264.
- A interface não foi testada por automação de navegador neste ambiente; seus endpoints e o fluxo de processamento foram exercitados nos testes da API.

## Alcance do resultado

O vídeo de referência mantém exatamente a composição aprovada. O motor novo é independente dos antigos caminhos locais e pode receber outros desenhos. Sua composição, câmera e apresentação seguem o padrão do projeto, com configurações próprias. Não há alegação de identidade pixel a pixel entre uma nova renderização e a versão histórica, nem de certificação de engenharia do tráfego ou da sinalização.
