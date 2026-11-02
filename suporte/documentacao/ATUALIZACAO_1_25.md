# Rodovia Studio 1.25 — catálogo QuickMapServices para escolher a melhor imagem aérea do trecho

## O que mudou
- Novo painel **Catálogo QuickMapServices (NextGIS)** em *2. Configuração → Fonte da imagem web*. Ele consulta a API pública do catálogo (`qms.nextgis.com/api/v1/geoservices/`).
- **Buscar** (Enter no campo também busca). Filtros disponíveis:
  - texto (ex.: ortofoto, satellite, Minas Gerais);
  - tipo: TMS/XYZ e/ou WMS;
  - **só os que cobrem o trecho**: usa a área do projeto convertida para WGS84, com 200 m de margem;
  - só os que estão funcionando, segundo o monitoramento do próprio catálogo;
  - só imagens aéreas ou de satélite: separa pelo nome e retira os mapas de ruas.
- **Ordem da lista**: primeiro imagens funcionando e de **cobertura local** (ortofotos estaduais ou municipais costumam ter resolução maior); serviços mundiais vêm depois.
- **Testar no trecho**: baixa uma amostra de 512 × 512 pixels no centro do trecho, na escala do zoom 19 (~0,28 m/pixel nesta latitude), e mostra:
  - a miniatura;
  - a **nitidez** (variância do laplaciano: mais detalhe, número maior);
  - o zoom testado;
  - a porcentagem de **falhas** (ladrilhos ausentes ou lisos).
- **Testar os 8 primeiros e ordenar pela nitidez**: compara os serviços lado a lado e põe o mais nítido em cima.
- **Usar**: o serviço passa a ser a fonte web do projeto no editor, no mosaico do vídeo e na aproximação (detalhe), pelo mesmo caminho XYZ/WMS da 1.19. Ao usar:
  - o crédito do serviço vai para a atribuição;
  - o link de licença ou termos fica registrado;
  - a imagem local (ECW, GeoTIFF), quando houver, continua por cima.
- **Detalhes e termos**: mostra tipo, EPSG, zoom, crédito, licença e termos do serviço.
- **Compatibilidade técnica nova**:
  - quadkey (`{q}`, Bing);
  - WMS 1.1.1 (SRS) além do 1.3.0;
  - WMS em PNG;
  - TMS com origem embaixo (`{-y}`);
  - endereços com `{switch:a,b,c}`.
- **Georreferência**: só são aceitos serviços em Web Mercator (EPSG:3857), o mesmo sistema dos ladrilhos atuais. Serviços em EPSG:3395 (ex.: Yandex) ou EPSG:4326 aparecem na lista, mas o botão Usar fica desligado e o motivo é mostrado.
- **Provedores com termos restritivos** (Google, Bing, Yandex, HERE, Mapbox e semelhantes): antes de usar, aparece uma confirmação de que a concessionária tem autorização. Sem a confirmação, nada muda.
- **Sem internet**: buscas e detalhes já feitos ficam em cache (`projetos\_ladrilhos\qms`), e os ladrilhos já vistos também.
- **Projetos existentes** continuam iguais. Os campos novos têm valores neutros e o cache de ladrilhos das fontes XYZ/WMS anteriores foi mantido.

## Medido neste ambiente
- **Testes**: **228 testes automáticos passaram** (222 da 1.24 + 6 novos), com o catálogo e os ladrilhos simulados:
  - quadkey (exemplo da documentação do Bing: x=3, y=5, z=3 → "213");
  - WMS 1.1.1/PNG;
  - cache das fontes antigas preservado;
  - parâmetros enviados à API (área do trecho, tipo, situação);
  - filtros e ordem;
  - cache sem internet;
  - conversões e recusas (EPSG:3395, WMS sem camada);
  - amostra (nitidez maior para imagem nítida que para desfocada, zoom menor dá menos detalhe, falhas contadas);
  - API completa (buscar, testar, usar, confirmação dos termos restritivos);
  - painel no Chromium: buscar com Enter, testar e ordenar, cancelar não muda nada, usar grava no projeto, reaplicar pelo formulário mantém a versão do WMS.
- **Formato real da API conferido** em 21/10/2026 nas respostas de três serviços (Esri 1300, Bing 5976 e um WMS 1576): campos `url`, `params`, `layers`, `format`, `z_max`, `y_origin_top`, extensão em EWKT. Os testes usam esses formatos.

## Não verificado / limitações
- **A busca e o download de ladrilhos reais pelo aplicativo não foram executados aqui**: este ambiente bloqueia `qms.nextgis.com` e os servidores de imagem. Falta conferir no seu computador; proxy ou bloqueio da rede corporativa podem impedir.
- **O catálogo não traz a data das imagens.** "Melhor" aqui é medido pela nitidez e pelas falhas no centro do trecho. Nitidez alta também pode vir de ruído ou compressão. Compare as miniaturas e confirme a data na fonte.
- **Não há garantia de imagem recente**: o QMS reúne serviços de terceiros. Para trechos em obra, o voo de drone ou aerolevantamento (ECW, 1.24) continua sendo a fonte mais atual.
- **Licença**: cada serviço tem seus próprios termos. O aviso automático cobre só os provedores conhecidos. Confira sempre o link de termos antes de usar em material da concessionária.
- Serviços que exigem chave (token) não funcionam sem a chave no endereço.
