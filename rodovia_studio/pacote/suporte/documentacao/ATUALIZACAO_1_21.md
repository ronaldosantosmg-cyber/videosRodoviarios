# Rodovia Studio 1.21 — pavimento rígido e flexível, representação escolhida, vídeo técnico ou artístico e contraste

## O que mudou

### 1. Pavimento rígido (concreto) ou flexível (asfalto)
- Em **Exportar vídeo → Perfil**, escolha o material separadamente para **pista nova**, **pista existente** e **acostamento**.
- **Pelo nome da camada do DXF**:
  - RIGIDO, CONCRETO, CCP, PCC ou WHITETOP → concreto;
  - FLEXIVEL, ASFALTO, CBUQ, CAUQ, TSD ou TSS → asfalto.
- **Nas áreas de pista do editor** (desenhar ou selecionar), cada área pode ter o material próprio: padrão do projeto, flexível ou rígido.
- **Concreto**:
  - placas com **juntas transversais a cada 5 m**, ajustáveis de 2 a 10 m;
  - as juntas ficam perpendiculares à pista ou ramo em que estão, e radiais nas curvas;
  - nas duas pistas paralelas ao eixo, as juntas são alinhadas pela estaca do eixo;
  - como direção local, o programa usa os centros de pista da rede (trevos, alças e acessos). No mosaico de visão geral (pixels de 1 m ou mais), o concreto aparece só com a cor.
- A legenda indica "(rígido)" quando todo o tipo é de concreto.

### 2. Representação do pavimento: escolher e alterar
Em **Perfil → Representação do pavimento**, para cada tipo (pista nova, existente, acostamento):

| Opção | Valores |
|---|---|
| Padrão | Automática (segue material e montagem), sólido, hachura diagonal, hachura cruzada, pontilhado ou placas de concreto com juntas |
| Cores | Preenchimento e hachura/juntas |
| Desenho | Espaçamento (m), ângulo (°) e espessura do traço (m) |

- Uma **amostra** ao lado mostra o padrão na hora.
- A hachura fica fixa nas coordenadas do projeto, nos ladrilhos de aproximação e no mosaico.
- Voltar para "Automática" desfaz a escolha.

### 3. Montagem do vídeo: técnico ou artístico
- **Artístico**: texturas realistas de asfalto e concreto, placas com leve variação de tom e juntas seladas escuras.
- **Técnico**: hachuras limpas de desenho:
  - asfalto novo com hachura dourada;
  - existente com hachura cinza-azulada;
  - concreto claro com juntas em traço e pontilhado de concreto, como no CAD.
- A opção "Aplicar também as texturas realistas sobre as hachuras" reproduz o visual técnico da 1.20. Projetos 1.20 que já estavam no técnico abrem com ela ligada.

### 4. Contraste projeto × imagem
- O controle **Contraste projeto × imagem** (0 a 100%) escurece e dessatura a imagem aérea, para o projeto se destacar.
- As cores do projeto não mudam. Em 0%, o vídeo fica como antes.

## Configuração
O esquema passou para a **versão 20**, com migração automática. Todos os novos campos começam como antes: flexível, juntas a 5 m, contraste 0 e representação automática.

## Medido neste ambiente
- **Testes**: 206 testes automáticos passaram no pacote 1.22 (196 da 1.20 + 7 da 1.21 + 3 da 1.22). Há 7 testes novos:
  - material pelo nome da camada, pelo padrão e pela área (os recortes mantêm o material);
  - juntas exatamente a cada 5 m, com variação de tom por placa e o traço técnico mais forte;
  - concreto no mosaico e nos ladrilhos;
  - contraste (o fundo escurece mais de 25% e a pista quase não muda);
  - hachura técnica limpa × com texturas, e a migração;
  - os padrões sólido, diagonal, cruzado e pontilhado, com as cores escolhidas;
  - editor: material da área, perfil, juntas, contraste e alteração da representação.
- **TH57 com concreto na pista nova**: as juntas aparecem transversais às faixas nas vistas de 25 m e 60 m, nos dois estilos (conferido nas imagens). A preparação da cena levou de 2,7 a 3 min, com o cache de geometria refeito.
- **TH57 com a configuração padrão**: quadros de 14, 40 e 96 s e vista do trevo idênticos ao pacote 1.20, pixel a pixel.

## Não verificado / limitações
- **Juntas longitudinais** (entre faixas) não são desenhadas como junta. Nesse lugar ficam as linhas de faixa pintadas.
- **Ramos sem rede de tráfego** (pavimento solto, sem trajetória): as juntas usam o eixo do DXF mais próximo e podem ficar inclinadas.
- **Cores**: são uma representação gráfica, não um padrão normativo. Ajuste-as em "Representação do pavimento", se a empresa tiver um padrão.
