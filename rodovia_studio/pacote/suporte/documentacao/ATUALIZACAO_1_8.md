# Rodovia Studio 1.8 — ajuda, estaqueamento completo, destaques e instalação organizada

## Como usar e dicas nos campos
- **❔ Como usar** (canto superior): guia passo a passo do projeto ao vídeo, com todas as ferramentas do editor, atalhos e atualização.
- **Dicas nos campos**: um **?** ao lado de cada campo explica o que ele faz (passe o mouse ou use Tab). A caixa “Dicas nos campos” liga e desliga os **?**, e a escolha fica gravada no navegador.

## Estaqueamento: automático ou pelo mouse, com início, fim e sentido
Em **Marcações do projeto → Estaqueamento (km)**:

| Modo | O que faz |
|---|---|
| **Automático** (padrão em projetos novos) | km a partir do início geométrico do eixo, no sentido do eixo. |
| **Manual** | Usa os pontos marcados no mapa. |
| **Desligado** | km só quando digitado, como na 1.2. É o que os projetos antigos sem início marcado recebem, para o vídeo não mudar. |

Ferramentas e opções:
- **📏 Início do km**: clique sobre o eixo. **Clique e arraste** ao longo do eixo para indicar o sentido de crescimento do km.
- **🏁 Fim do km** (novo): clique onde vale o km final. Com início e fim marcados, o sentido é automático e prevalece sobre a seta.
- **Ajuste proporcional**: distribui a diferença entre o km final informado e a distância medida (km = km inicial + sentido × fator × distância). Útil quando os marcos oficiais não batem com a geometria. Se a combinação de km e sentido for impossível, o aplicativo recusa com mensagem.
- O painel mostra o sentido, o fator, o **km medido no fim** e a diferença para o km final informado. Os botões **Inverter sentido** e **Usar km final medido** completam o ajuste.
- O editor desenha o início (◆), o fim (■) e uma seta amarela no sentido do km. A exportação ganhou o ponto **Fim do estaqueamento** (layer RS_FIM_KM).

## Destaques (pontos especiais) com linha de chamada
- Ferramenta **⭐ Destaque**:
  - escolha o tipo: edificação, interferência, poste, rede, drenagem, acesso ou ponto especial;
  - nome e descrição são opcionais;
  - clique no ponto; **clique e arraste** para posicionar a caixa de informação;
  - arraste uma caixa existente para movê-la.
- No vídeo, cada destaque tem marcador colorido com a letra do tipo, **linha de chamada** e caixa com nome, tipo, km e descrição. A caixa **surge e some suavemente** quando o ponto entra e sai do quadro, inclusive durante as transições e o percurso. Sem posição escolhida, a caixa fica ao lado do ponto.
- Na lista de marcações, cada destaque permite editar nome, tipo, descrição e cor, e marcar **no vídeo**, **mostrar km** e **parada da câmera**. Com parada, o vídeo para no destaque e mostra o nome no cabeçalho. Há também **Caixa automática**, **Ver** e **Excluir**, com desfazer/refazer.
- Exportados e reimportados em GeoJSON, KML/KMZ e DXF (layer RS_DESTAQUE).

## Instalação organizada e atualização fácil
A pasta do aplicativo fica assim:
```
Rodovia_Studio\
  ABRIR RODOVIA STUDIO.cmd        <- executor principal (cria o atalho "Rodovia Studio" na Área de Trabalho)
  ATUALIZAR RODOVIA STUDIO.cmd    <- aplica o ZIP de atualização mais novo
  LEIA-ME.txt
  projetos\                       <- seus projetos, CAD/KMZ e vídeos (antes: dados\)
  atualizacoes\                   <- salve aqui os ZIP de atualização (Downloads também é verificado)
  suporte\sistema\                <- programa, Python portátil, bibliotecas, recursos e testes
  suporte\documentacao\           <- manuais, notas de versão e imagens de conferência
  suporte\backups\                <- o que cada atualização substituiu
  suporte\logs\                   <- instalação, atualização e erros
```
- **Primeira vez (a partir da 1.2 a 1.7):** extraia o ZIP fora da pasta do aplicativo e rode **INSTALAR_ATUALIZACAO.cmd**. Ele pede a pasta e reorganiza tudo **sem apagar nada**:
  - o que mudou de lugar vai para a pasta nova;
  - os iniciadores antigos vão para `suporte\backups\legado_<data>`;
  - `dados` passa a se chamar `projetos`;
  - se algum arquivo estiver em uso, ele desfaz os movimentos e avisa.
- **Próximas vezes:** salve o ZIP em `atualizacoes` (ou deixe em Downloads) e dê dois cliques em **ATUALIZAR RODOVIA STUDIO**.
  - Ele procura o ZIP de versão mais nova, verifica se o aplicativo está fechado, guarda o que for substituído em `suporte\backups` e move o ZIP aplicado para `atualizacoes\aplicadas`.
  - Se o pacote trouxer um atualizador mais novo, é ele que aplica a atualização.
- O atualizador roda com uma cópia temporária do Python portátil, para poder mover a pasta do Python sem conflito.

## Medido
- **86 testes passaram**: os 76 da 1.7 e 10 novos — estaqueamento automático/manual/fim/sentido/ajuste, migração, km nos itens, destaques no vídeo (caixa, marcador, parada, oculto), exportação/reimportação de destaques e fim do km, página de ajuda, reorganização de instalação antiga sem perda de arquivos, desfazer em caso de arquivo em uso, busca do ZIP mais novo com troca de atualizador, e pasta de projetos.
- Teste de interface em Chromium: início do km arrastado (sentido contrário), fim do km, km medido, destaque com caixa arrastada, desfazer/refazer, mais de 30 dicas, dica do CRS e janela Como usar.
- TH57 sem marcações novas: o modo de qualidade Anterior continua igual à 1.2 (conferido no quadro de 14 s, 2560×1440).

## Não testado / limites
- Os scripts do Windows (`INSTALAR_ATUALIZACAO.cmd`, `instalar.ps1`, `atualizar.ps1`, os dois `.cmd` principais e o atalho na Área de Trabalho) **não foram executados no Windows**. A lógica de mover, copiar e fazer backup está em Python e foi testada aqui.
- Se o OneDrive estiver sincronizando a pasta no momento da reorganização, algum movimento pode falhar. O atualizador desfaz e pede para tentar de novo.
- O atalho pode ficar sem ícone se o OneDrive redirecionar a Área de Trabalho; o executor principal continua funcionando.
