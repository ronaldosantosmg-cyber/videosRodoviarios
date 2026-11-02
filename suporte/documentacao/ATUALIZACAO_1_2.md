# Rodovia Studio 1.2 — atualização integrada

Instalação: feche o aplicativo, execute ATUALIZAR.cmd e selecione a pasta RodoviaStudio existente. Abra INICIAR.cmd, aguarde a preparação automática da dependência nova e pressione Ctrl+F5 no navegador. Sem administrador. Seus projetos e vídeos são preservados; os programas substituídos recebem backup.

## Representação

- Corte vermelho, aterro verde: preenchimento, hachuras e contorno reforçados. Limpezas configuradas continuam aplicadas.
- Via existente em cinza claro (#a4a8a9); projetada em cinza escuro. Layers HPAV/PAVIMENTO com EXIST são classificadas como existente inclusive em configurações antigas.
- Canteiro e barreiras usam exclusivamente os polígonos do CAD: não é criada uma largura de separação. TH57: 128 entidades GE_SC-HCANTEIRO e 2 GE_SC-HNEWJERSEY. Conferência feita no DXF disponível, não no DWG original.
- Legenda fixa no cabeçalho com os elementos presentes no enquadramento. Rodapé continua só com km inicial/final, extensão e ano.
- Passarelas com rampas, patamares e guarda-corpos; cadastro de baias esquemáticas preservado.

## Hidrografia

Consulta por área: nomes/eixos IBGE BC250/2025 (escala 1:250.000) e polígonos de água OpenStreetMap. A textura azul é aplicada aos polígonos, com textura fixa no terreno; não se inventam margens a partir da largura de um eixo. Sem polígonos, só há uma linha cartográfica fina. Nomes não cadastrados não são inventados. Há cache local e dados incluídos para o TH57. A fonte é cartográfica, não levantamento de margens ou estudo hidráulico.

Fontes consultadas em 18/10/2026:
- https://geoservicos.ibge.gov.br/geoserver/ows
- https://www.ibge.gov.br/geociencias/cartas-e-mapas/bases-cartograficas-continuas/15759-brasil.html
- © OpenStreetMap contributors, dados sob ODbL: https://www.openstreetmap.org/copyright
- API de consulta: https://overpass-api.de/api/interpreter

O GeoJSON distribuído mantém essas atribuições. A consulta não modifica dados externos.

## Tráfego e retornos

O crescimento do km define a orientação longitudinal. A pista fisicamente à direita recebe fluxo crescente; a oposta, decrescente. A direção não depende da ordem dos vértices do CAD. Marginais adotam o sentido da pista adjacente. Ilhas detectadas orientam a circulação; cruzamentos em OAE não viram conexões de nível pelo simples cruzamento em planta.

O grafo combina eixos nativos com trajetórias derivadas das superfícies de pavimento. Cada veículo segue um itinerário contínuo, incluindo retornos quando existe conexão segura. Conectores e corpo inteiro do carro são verificados dentro do pavimento, fora de canteiros, barreiras e exclusões. Não há troca aleatória de faixa. Trechos sem conexão validada ficam sem veículos e geram aviso, em vez de receber saltos ou atalhos.

Na prévia, abra Conexões de tráfego e retornos para mostrar trajetórias validadas ou traçar um eixo complementar dentro do pavimento existente. Informe nível distinto para vias em desnível. Uma trajetória desenhada pelo usuário continua sujeita à validação; não cria asfalto.

A extração automática não certifica todos os movimentos de um projeto: arquivos sem eixos completos, superfícies separadas, lacunas e detalhes ambíguos podem exigir complemento. A animação é ilustrativa, sem simulação de demanda ou de conflitos de tráfego. O diagnóstico fica em traffic_network.json no projeto.

## Vídeos curtos

Abaixo de 45 s, o modo automático usa vista geral estável, zoom discreto e aparecimento com suavização. Assim, não comprime um sobrevoo inteiro em poucos segundos. A opção Sobrevoo completo continua disponível. Duração e fps pedidos são mantidos. Para 202 s, o cronograma de câmera original permanece.

## Limpeza e desempenho

Manutenção → Ver espaço recuperável / Limpar caches e temporários. Remove só cache_geometria, imagery, hidrografia e uploads/MP4 parciais interrompidos. Bloqueia limpeza durante tarefas ativas. Não remove CAD, KMZ, configurações, vídeos finais, banco de projetos ou arquivos fora do aplicativo. A primeira geração posterior recalcula os caches e pode demorar mais. Libera espaço em disco; não promete aumentar a velocidade de renderização. Novas instalações de dependências não mantêm cache do pip. A legenda é calculada de forma vetorizada para evitar milhares de operações Python em cada quadro.

## Validação

21 testes passaram: vídeo/API/cache, sentido físico à direita com eixo invertido, itinerário contínuo por retorno, bloqueio em cruzamento em OAE, cache de hidrografia, canteiro do CAD sem alteração, classificação da via existente, vídeos curtos, rampas/baias e limpeza preservando originais/exportações. JavaScript passou na verificação de sintaxe. Wheel Windows x64/Python 3.12 da dependência scikit-image 0.26 foi obtido; instalador Windows não executado neste ambiente.

Quadros reais do TH57 gerados com a revisão integrada. O MP4 de referência aprovado permanece original; Exportar referência idêntica continua sendo cópia binária e não aplica as alterações. Para usar as melhorias, escolha Gerar novo vídeo. Não foi produzida uma nova exportação completa de 202 s nesta atualização.
