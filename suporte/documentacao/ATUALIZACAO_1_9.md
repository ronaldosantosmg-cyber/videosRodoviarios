# Rodovia Studio 1.9 — editor sobre imagem web (Esri) com DXF/KMZ simplificado

## O que mudou
A imagem de trabalho do editor deixou de depender da prévia renderizada. Depois de **Analisar arquivos**, a seção 3 abre sobre a imagem de satélite **Esri World Imagery** em ladrilhos (a mesma fonte do fundo “Esri online” do vídeo), que carregam no nível de detalhe do zoom atual — a imagem fica nítida de perto, sem pixelar como a prévia. Por cima, o **DXF e o KMZ simplificados** são desenhados como linhas finas por classe.

- **Fundo de edição** (acima da barra de ferramentas):
  - **Imagem web (Esri) + vetores do DXF/KMZ** — padrão quando o projeto foi analisado;
  - **Prévia renderizada** — a imagem do vídeo, como antes (disponível depois de gerar a prévia);
  - **Só vetores** — sem imagem, útil sem internet.
  Ao trocar o fundo, o mesmo ponto continua no centro, na mesma escala. A escolha fica gravada no navegador.
- **Camadas**: liga/desliga pavimento, pavimento existente, acostamento, canteiro, barreira, OAE, corte, aterro, faixa de domínio, eixos, DXF adicionais e KMZ (com a quantidade de elementos). Há controles de transparência para a imagem e para os vetores.
- **Sem prévia**: o eixo vem da análise, então **Início do km** (com sentido arrastado), **Fim do km**, **OAE**, **Destaque**, **Intervenção**, **Linha de chamada**, **Sentido**, **Exclusões**, **Sem conexão** e **Par de controle** funcionam logo após “Analisar arquivos”. O cursor já mostra km e distância ao eixo. As ferramentas que dependem das trajetórias de veículos (inverter/desativar fluxo, cabine) continuam pedindo a prévia.
- **Pares de controle sobre a imagem web**: clique o ponto nos vetores do DXF e depois o mesmo ponto na imagem. Com o fundo web, **Aplicar ao DXF** e **Reverter** só reanalisam o projeto (segundos) e os vetores se deslocam; não é preciso renderizar a prévia.
- **Cache de ladrilhos**: cada ladrilho baixado fica em `projetos\_ladrilhos` e é reutilizado sem internet. Sem internet e sem cache, o rodapé avisa “sem internet/cache nesta área” e o editor segue com os vetores (nova tentativa a cada 30 s). “Limpar cache” da manutenção também apaga esses ladrilhos (eles são baixados de novo quando necessário).
- O rodapé do editor mostra a atribuição exigida da imagem (Esri, Maxar, Earthstar Geographics e GIS User Community). O uso dos ladrilhos segue os termos da Esri, como o fundo “Esri online” que o vídeo já usava.

Tudo continua salvo na configuração **em coordenadas do CRS do projeto**, com desfazer/refazer; o DXF original não é alterado. Nenhuma marcação muda por causa do fundo escolhido. O esquema de configuração não mudou (versão 8), por isso não há migração nova.

## Como funciona (técnico)
- O navegador trabalha em Web Mercator, como os ladrilhos. A conversão entre o CRS do projeto e Web Mercator usa polinômios de 3º grau ajustados pelo pyproj na área do projeto (com 35% de margem), nos dois sentidos (`/api/projects/{id}/geo`, guardado em `geo.json`).
- Os vetores (`vectors.json`) são gerados na análise e na prévia, com o ajuste DXF já aplicado, simplificados com tolerância de 0,25 m; o eixo principal vai reamostrado a cada 2 m para as ferramentas de km.
- Os ladrilhos passam pelo próprio servidor local (`/tiles/esri/z/y/x`), que valida a resposta (JPEG/PNG) antes de gravar no cache e responde 404 quando não há internet nem cache.
- Nível de ladrilho escolhido pelo zoom (máximo 19); enquanto um ladrilho carrega, é mostrado o nível anterior já baixado, ampliado.

## Medido neste ambiente
- Conversão CRS ↔ Web Mercator: erro máximo **< 5 mm** em 300 pontos aleatórios contra o pyproj para áreas de 300 m, 20 km × 10 km (EPSG:31983) e 50 km × 30 km (EPSG:31982). No TH57: 0,0002 mm (ida) e 0,0002 mm (volta). No navegador, ida e volta tela→CRS < 2 mm e a conversão em JavaScript coincide com o pyproj (< 5 mm).
- TH57: análise 15,4 s; `vectors.json` com 32.682 vértices (954 kB); desenho completo do editor (vetores + ladrilhos) ~2 ms por quadro no Chromium de teste.
- Testes automáticos novos (`tests/test_v19.py`, 7): ajuste de coordenadas, cache e validação de ladrilhos, servidor sem internet (404) e com cache (200), vetores após a análise (classes, eixo, simplificação do arco), deslocamento dos vetores com o ajuste DXF aplicado sem prévia, DXF original intacto, e o editor no navegador **sem prévia** (início do km com sentido, OAE, destaque, par de controle, camadas, troca de fundo mantendo o centro, gravação na configuração).
- Teste da interface anterior (`test_ui_smoke`) segue passando com o novo fundo padrão.

## Não verificado
- **Ladrilhos reais da Esri não foram carregados neste ambiente** (o acesso a server.arcgisonline.com é bloqueado aqui). Os testes usam ladrilhos simulados; o endereço é o padrão do serviço World Imagery (`/tile/{z}/{y}/{x}`) e o mesmo servidor já fornece a imagem do vídeo. Confira no seu PC na primeira abertura.
- Não verifiquei a disponibilidade do nível 19 em todo o trecho: onde a Esri não tem imagem nesse nível, o próprio serviço devolve um ladrilho “sem dados”; afaste um pouco o zoom.
- Desempenho em PCs mais fracos e com conexões lentas não foi medido.
- Os scripts do Windows (.cmd/.ps1) não foram executados aqui; a atualização foi simulada sobre as organizações 1.8 e antiga.
