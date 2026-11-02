# Rodovia Studio 1.27 — edição direta, texturas por área, caixas de chamada ajustáveis, menu da seleção, fluxos, velocidade de avanço e janela própria do Windows

## Como as versões ficam organizadas (para chegar a um aplicativo Windows)
O Rodovia Studio tem três partes, cada uma com a sua versão. Todas aparecem em **Ajuda › Sobre**.

| Parte | Versão atual | Quando muda | Como chega ao seu computador |
|---|---|---|---|
| **Programa** (arquivos .py/.js/.html em `suporte\sistema`) | 1.27.0 | a cada atualização | ZIP em `atualizacoes` + ATUALIZAR (ou o .exe aplica sozinho) |
| **Formato do projeto** (esquema da configuração) | 24 | quando surgem campos novos | conversão automática ao abrir; projetos antigos mantêm o resultado anterior |
| **Iniciador** (`Rodovia Studio.exe`) | 1.1 | raramente | o aviso “Nova versão do iniciador” pede para executar COMPILAR INICIADOR.cmd |

Assim o .exe continua pequeno e estável, e as melhorias chegam pelos ZIPs, sem reinstalar.

## O que mudou
### Seleção e edição direta (como num programa de desenho)
- **Clique e arraste:** um clique sobre o objeto seleciona e já permite arrastar. Não é preciso clicar duas vezes.
- **Grips em destaque:** aparecem quadrados maiores com contorno. O grip sob o cursor fica laranja e, ao arrastar, vermelho. Áreas ganham um preenchimento leve.
- **Alça redonda de giro:** fica acima da seleção. Arrastar gira em torno do centro; com Shift, em passos de 15°.
- **Mini-barra junto da seleção:** mover, girar, copiar, trocar textura, trocar nome, propriedades e apagar.
- **Teclado:**
  - setas deslocam 0,10 m (Shift: 1 m; Ctrl: 0,01 m);
  - Delete apaga.
- **Seleção múltipla:** Shift+clique soma objetos; arrastar qualquer um move todos; a alça gira o conjunto.

### Áreas do desenho: trocar textura, nome e tipo
- **Selecionar:** clique sobre uma área fechada do DXF, como a pista (Alt+clique quando houver um fluxo por cima). A área fica destacada com os vértices exatos.
- **Botão direito** abre:
  - **Trocar textura…**
  - **Trocar nome…**
  - **Trocar tipo** (pista nova, existente ou acostamento)
  - **Tornar editável (grips)**
  - **Ocultar a camada**
- **O DXF não é alterado.** A troca cria uma “área de pista” com os mesmos vértices, que vale por cima do desenho.
- **Diálogo de textura:**
  - tipo e material;
  - grão, tom, remendos, fissuras e brilho, com amostra ao vivo;
  - aplicar **só à área** (textura própria) ou **a todas as áreas do tipo**.
  - Enter aplica; Esc cancela.
- **No vídeo:** cada área com textura própria recebe um código de superfície exclusivo e sai com a sua textura, inclusive na aproximação (ladrilhos de detalhe).

### Caixas de chamada (destaques e pórticos)
- **Losango amarelo:** fica no centro da caixa. Arraste-o para mudar a posição; a linha de chamada aumenta ou diminui. O editor mostra o comprimento da linha.
- **Propriedades:** **Linha de chamada (m)** e **Direção da caixa (°)**; Enter confirma.
- **Caixa automática:** volta ao posicionamento automático sem sobreposição.

### Menu do botão direito
- **Largura fixa** (300 px).
- **Com seleção, mostra só os comandos da seleção:**
  - objetos: trocar textura (áreas), trocar nome, mover a caixa de chamada, propriedades/atributos, mover, girar, copiar, escala, espelhar, paralela, copiar propriedades, apagar;
  - trajetória: inverter, desativar, velocidade, editar traçado, ligações;
  - ligação: proibir ou permitir;
  - área do desenho: os comandos acima.
- **Botão direito sobre um objeto não selecionado:** seleciona o objeto primeiro, como no Windows.
- **Sem seleção:** comandos gerais (inserir, desfazer, enquadrar, prévia, ajuda).

### Fluxos de tráfego
- **Ligações nos cruzamentos:**
  - ao selecionar uma trajetória aparecem as **saídas (verde)** e as **chegadas (azul)**;
  - clique numa ligação para **proibir** o movimento ou, se já proibido (vermelho tracejado), **permitir de novo**;
  - **Forçar ligação** (ferramenta em *Fluxos*): liga dois trechos cujas pontas estão a até 30 m;
  - as regras ficam salvas (`connection_rules`), com grips para ajustar.
- **Velocidade por trecho:** na trajetória selecionada, informe o limite em km/h. Os fluxos desenhados também aceitam velocidade.
- **Editar traçado:** converte a trajetória calculada num fluxo desenhado com grips e desativa a calculada.
- **Movimento dos veículos:** com “Veículos reduzem nas curvas e ligações”, cada veículo respeita uma velocidade de curva (aceleração lateral de 2,2 m/s²) e freia antes da curva.
  - **Projetos novos:** ligado.
  - **Projetos antigos:** desligado, para manter o movimento da 1.26.

### Velocidade de avanço da apresentação sobre a imagem
- **Perfil de vídeo → Avanço da câmera:**
  - **pela duração digitada** (como antes);
  - **pela velocidade de avanço** (km/h equivalentes sobre a imagem): a duração do vídeo é calculada.
- A linha de informação mostra o percurso, o tempo e a velocidade resultantes.
- **Ferramenta Velocidade de avanço (trecho):** clique no início e no fim do trecho sobre o eixo e escolha a porcentagem. Por exemplo, 40% faz a câmera levar 2,5 vezes mais tempo sobre aquela obra. Vários trechos podem ser combinados.

### Janela do Windows
- **Barra de menus:** Arquivo, Editar, Exibir, Inserir, Ferramentas, Ajuda.
- **Barra de status:** ferramenta, seleção, SNAP/ORTO clicáveis, coordenadas, estado de salvamento e versão.
- **Ajuda › Sobre** mostra as versões.
- **Rodovia Studio.exe 1.1 (janela própria):**
  - Ao recompilar com **COMPILAR INICIADOR.cmd**, o programa abre numa **janela própria do Windows (WebView2)**: sem navegador, sem barra de endereço, com o ícone do programa.
  - A janela guarda o tamanho e a posição; “Duas janelas” abre outra janela própria.
- **De onde vêm as DLLs:** o componente WebView2 (Microsoft.Web.WebView2 1.0.2903.40) é procurado em `suporte\sistema\webview2`, depois num `.nupkg` em `suporte\sistema\pacotes_webview2` e, por fim, baixado do nuget.org.
- **Sem o componente:** o .exe é compilado como antes e abre no Edge em modo aplicativo.

## Medido neste ambiente
- **Testes:** **245 testes automáticos passaram** (236 da 1.26 + 9 novos). Os novos cobrem:
  - modelos e migração;
  - redução nas curvas (curva de 30 m de raio: ~8,1 m/s; frenagem antecipada);
  - proibir e forçar ligações;
  - velocidade por trecho, com a simulação mais lenta no trecho;
  - textura própria de área no quadro (código de superfície exclusivo, área mais escura com brilho −0,25);
  - área do desenho e Sobre pela API;
  - velocidade de avanço (mapeamento e duração calculada);
  - código do iniciador em C# 5 com o bloco WebView2 isolado;
  - teste de tela no Chromium:
    - área do desenho, menu só da seleção com largura de 300 px, troca de textura e nome;
    - arrastar o destaque direto, setas, losango da caixa e linha de 25 m;
    - alça de giro e desfazer;
    - selecionar trajetória e proibir ligação;
    - modo por velocidade, trecho de avanço e Ajuda › Sobre.
- **Regressão TH57:** padrão idêntico pixel a pixel à 1.26; motor “anterior” idêntico à 1.23.
- **TH57, 120 s de simulação com a redução nas curvas:**
  - 21% dos pontos dos itinerários ficam limitados pela curva;
  - velocidade média de 17,1 m/s (sem a redução: 17,6);
  - 5% mais lentos: 13,2 m/s (sem a redução: 14,6);
  - nenhuma colisão traseira nos dois casos.

## Não verificado / limitações
- **Iniciador 1.1:** não foi compilado nem executado aqui (não há compilador C# neste ambiente). No Windows:
  - o download do nuget.org pode ser bloqueado pela rede da empresa; nesse caso coloque o `.nupkg` em `pacotes_webview2`;
  - o **Microsoft Edge WebView2 Runtime** precisa estar instalado (vem com o Windows 10/11 atualizado). Sem ele, o programa avisa e abre no navegador.
- **Forçar ligação:** só liga **pontas** de trechos. Para ligar no meio de um trecho, desenhe um fluxo.
- **Limite de velocidade por trecho:** vale no modelo de tráfego “simulado”, não no “anterior”.
- **Áreas com textura própria:** no máximo 200 áreas.
- **Trilhas de roda:** na pista existente com textura própria não aparecem trilhas de roda.
- **Modo por velocidade de avanço:** com paradas nas obras, a velocidade informada é aproximada. Vídeos calculados com menos de 45 s ficam com 45 s (abaixo disso o vídeo curto usa a vista geral).
