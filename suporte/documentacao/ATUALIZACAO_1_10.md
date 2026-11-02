# Rodovia Studio 1.10 — vídeo limpo, setas por km/conflito, marcos, sentido, grama e cidades

Esta é a **primeira etapa** dos pedidos. As etapas seguintes estão no fim deste documento.

## Sujeiras de sinalização (marcadas em vermelho na imagem enviada)
As sobras vinham da pintura automática de faixas e das setas: o aplicativo desenha bordas, eixos e setas sobre as trajetórias calculadas do pavimento. Nas junções, ramos curtos dessas trajetórias se cruzavam e geravam traços soltos, “letras” e setas tortas.

- **Pintura Limpa** (padrão, em *Exportar vídeo → Sinalização, setas e anotações*):
  - trechos curtos (menos de 25 m) não recebem pintura;
  - traços de trajetórias diferentes que se cruzam ou se sobrepõem são removidos, e fica o da via mais longa;
  - perto de convergências, divergências e rotatórias só a via principal mantém a pintura.
- **Ferramenta 🧽 Sem sinalização** (editor): desenhe com o mouse a área onde não deve haver pintura nem setas. O pavimento continua. Serve para qualquer sobra que ainda apareça. Tem desfazer/refazer, edição de vértices (**Editar vértices**) e exclusão pela lista. Fica salva em coordenadas do CRS e não altera o DXF.
- **Pintura Anterior** reproduz a 1.9.

## Setas de fluxo a cada km e nos conflitos
- **Padrão**: nas vias principais e marginais, uma seta a cada **1.000 m** (espaçamento ajustável de 100 a 5.000 m), mais uma no início. Nos **pontos de conflito** (convergências, divergências, rotatórias e ligações entre vias), uma seta antes e outra depois. Setas no mesmo sentido a menos de 12 m são unidas.
- **Outras opções**: “Frequentes (anterior)” ou “Sem setas”.

## O que aparece no vídeo
O vídeo já mostrava:
- pavimentos, sinalização, taludes (corte e aterro), obras, acostamentos e barreiras;
- veículos e faixa de domínio;
- nomes dos destaques e km das intervenções.

Novidades (todas podem ser desligadas):
- **Marcos do km inicial e final** sobre o traçado: haste com bandeira e “Início • km 325+850” / “Fim • km 335+000”. Usam o estaqueamento ativo; sem estaqueamento, ficam no início e no fim do eixo.
- **Seta no topo** com o *Sentido do estaqueamento (km crescente)*. Ela gira conforme a câmera percorre o traçado.
- **Grama nos canteiros** (qualidade Aprimorada): textura em metros, que não “nada” com a câmera.
- **Cidades próximas**:
  - dentro do quadro, aparecem com ponto e nome;
  - fora do quadro, uma seta na borda indica a direção e a distância (até o raio configurado, padrão 25 km).
  - **Marcar à mão**: ferramenta **🏙 Cidade**.
  - **Buscar automaticamente**: botão **Buscar cidades próximas (OpenStreetMap)**, que traz cidades e vilas, mais os povoados a até 8 km. O resultado fica guardado no projeto.
  - Na lista dá para renomear, ocultar ou excluir.
  - Exportadas e reimportadas em GeoJSON/KML/KMZ/DXF (camadas RS_SEM_SINALIZACAO e RS_CIDADE).

## Proteções contra divisão por zero e entradas vazias
- **Eixo com menos de 10 m**: mensagem clara (antes, erro interno do numpy).
- **Eixo fechado** (início igual ao fim): a câmera usa a direção principal dos pontos. Antes havia divisão por zero.
- **Teste automático com entradas degeneradas**: eixo curto, fechado, com pontos repetidos, pavimento degenerado, sem eixo, início e fim do km no mesmo ponto, cidade sobre o eixo. O teste roda com avisos de divisão por zero tratados como erro. Resultado: mensagem clara ou quadro válido, sem NaN.
- **Já existentes e conferidos**: ajuste proporcional do km (ignora início e fim com menos de 1 m), escala do editor, distâncias do tráfego e lista vazia de quadros na exportação PNG.

## Configuração
O esquema passou para a **versão 9**, com migração automática: projetos antigos abrem com os novos padrões. Para o vídeo ficar exatamente como na 1.9, escolha:
- “Pintura: Anterior”;
- “Setas: Frequentes”;
- marcos, seta de sentido e grama desligados.

## Medido neste ambiente
- **TH57**:
  - traços de pintura: 26.972 → 19.192;
  - setas: 388 → 154;
  - tempo de preparo da cena: +1 s aproximadamente.
- Imagem antes/depois em `conferencia/v1_10_sinalizacao_antes_depois_TH57.jpg` (o trevo com rotatórias da imagem enviada).
- **Regressão**: com as opções “Anterior” e as anotações desligadas, os quadros TH57 de 14, 40 e 96 s e a vista do trevo são **idênticos** aos da 1.9, pixel a pixel.
- **Testes**: 107 automáticos passaram (14 novos).

## Não verificado
- **Busca de cidades no OpenStreetMap**: não tive acesso ao serviço neste ambiente, então os testes usam respostas simuladas. No seu PC, a primeira busca precisa de internet. Se a rede bloquear, o aplicativo avisa e a ferramenta Cidade continua funcionando.
- **Nomes de cidades do TH57**: na imagem de conferência são exemplos (“Cidade A/B (teste)”), não as posições reais.
- **Sobras de pintura**: a remoção automática foi conferida no TH57 nos trechos que inspecionei. Pode restar alguma sobra em outros projetos; nesse caso, use a área **Sem sinalização**.
- **Vídeo completo do TH57**: não foi gerado nesta etapa, só quadros de conferência.

## Próximas etapas (combinadas)
- **1.11 — tráfego**:
  - veículos sem colisão traseira (distância mínima com desaceleração);
  - travessia do canteiro só em retornos em desnível, em nível ou em locais indicados;
  - aumento do fluxo para simular engarrafamento;
  - bloqueio parcial de faixas com retenção;
  - rotas alternativas.
- **1.12 — dia/noite e duas janelas**:
  - transição de dia para noite com faróis e sinalização em destaque;
  - duas janelas sincronizadas: uma de configuração e outra de visualização e resultados.
- **Logotipo GeoRas**: entra quando você enviar o arquivo, na outra conversa.
