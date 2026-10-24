# Rodovia Studio 1.37 — abrir DWG, vegetação, pedestres e frota variada (estilo Twinmotion, parte 2)

## Abrir DWG junto com DXF
- **Onde:** o botão **Escolher DXF/DWG…** (seção Projeto e faixa **Início › Arquivos › DXF/DWG…**) e o arrastar-e-soltar aceitam **.dwg**.
- **Como funciona:**
  - o programa converte o DWG em DXF com o **ODA File Converter**, gratuito, da Open Design Alliance, instalado uma vez no computador;
  - roda localmente, sem internet;
  - depois segue como com um DXF: camadas, análise, edição e vídeo.
  - A lista de arquivos mostra “convertido do DWG”.
- **O original não muda:** o DWG não é alterado; uma cópia fica no projeto (`input.dwg`) e o DXF convertido em `input.dxf`. Enviar um DXF depois substitui o convertido.
- **Onde o programa procura o conversor:**
  - na instalação padrão do Windows (`Arquivos de Programas\ODA\ODAFileConverter…`);
  - em `sistema\ferramentas\ODAFileConverter\`;
  - ou no caminho da variável `RODOVIA_ODA`.
- **Sem o conversor:** uma janela explica onde baixar. A alternativa é o AutoCAD/Civil 3D: Salvar como › DXF.

## Vegetação (ferramenta 🌳 Vegetação, comando `ARVORE`)
- **Tipos:** árvore, ipê amarelo (florido), eucalipto (copa estreita), palmeira, arbusto e cerca-viva.
- **Três modos:**
  - **Árvore avulsa:** um clique, uma planta.
  - **Pincel:** arraste para plantar ao longo do caminho, no espaçamento escolhido, com leve dispersão. Um Ctrl+Z desfaz o traço inteiro.
  - **Área:** clique os vértices e Enter. As plantas são espalhadas pela densidade (plantas por 1000 m²), sempre no mesmo arranjo, e **não entram sobre pista, acostamento ou OAE**.
- **Propriedades:** a área pode ser selecionada e editada como as outras marcações (tipo, densidade, tamanho, sorteio).
- **No vídeo:** copas em tufos, iluminadas do lado do sol, com sombra no chão que segue a hora do sol (quando “Sombras pela hora do sol” está ligado). Aparecem com a câmera a menos de 4 km de largura de vista.

## Pedestres
- **Onde aparecem:**
  - atravessando as **faixas de pedestre**;
  - subindo e descendo as **passarelas** (rampa, tabuleiro, rampa);
  - nos **caminhos de pedestres** (ferramenta 🚶, comando `PEDESTRES`: clique os pontos da calçada ou trilha e Enter).
- **Movimento:** vão e voltam nos dois sentidos, com velocidades diferentes; de perto, pernas e braços alternam.
- **Visibilidade:** aparecem com a câmera próxima (vista de até 900 m). As pessoas são desenhadas um pouco maiores que o real, para aparecerem no vídeo.

## Frota variada
- **Veículos:** carros, **picapes**, **vans**, **motos**, caminhões, **carretas** (18,6 m) e ônibus, com proporções típicas de rodovia.
- **Ramos e acessos:** ficam com carros, motos, vans e picapes.
- **Simulação:** cada tipo tem comprimento e velocidade próprios (carretas mais lentas, motos um pouco mais rápidas).
- **Frota clássica:** a opção “Clássica” mantém carros, caminhões e ônibus como antes.
- **Onde escolher:** painel **Vídeo › Câmera, clima, sol, vida e antes/depois** (pedestres e frota).

## Projetos existentes
- **Sem mudança no vídeo:** continuam com a frota clássica e sem pedestres (formato do projeto 29). Para ligar, use o painel Vídeo.

## Medido neste ambiente
- **Testes automáticos:** **306** passaram (301 da 1.36 + 5 novos). Os novos testes cobrem:
  - conversão do DWG com um conversor de teste (DXF gerado, cópia do DWG, aviso sem conversor, arquivo que não é DWG);
  - API (DWG convertido, indicação “convertido”, DXF posterior substitui);
  - esquema 29 e frota (clássica como antes, variada com os 7 tipos, desenho dos novos veículos);
  - vegetação e pedestres no vídeo:
    - área plantada sem invadir a pista;
    - sombra que muda com a hora;
    - pedestres andando no caminho e na faixa;
    - nada muda com os pedestres desligados;
  - um teste de tela:
    - DWG aberto e analisado;
    - árvore, pincel (um Ctrl+Z desfaz o traço), área com Enter;
    - caminho de pedestres liga os pedestres;
    - densidade nas propriedades;
    - gravação.
- **Testes anteriores ajustados:** o teste de congestionamento da 1.12 passou a fixar a frota clássica, como quando foi escrito; com a frota variada, também se verifica que o congestionamento reduz a velocidade (cerca de 8 %, contra 13 % na clássica, porque os veículos longos ocupam a via).
- **Correção durante a versão:** a geração em vários processos (vídeo e cabine) falhava com a frota variada. Corrigida, e coberta pelos testes de geração em paralelo.
- **Vídeo TH57 (projeto existente):** quadros 14, 40 e 96 s e vista do trevo **idênticos** à 1.36, pixel a pixel.
- **Tempo por quadro (TH57 1280×720, quadros 40, 60 e 80 s):**
  - sem nada: 0,22 / 0,52 / 0,44 s;
  - com frota variada e pedestres: 0,16 / 0,35 / 0,43 s;
  - com uma mata de 1361 árvores, frota e pedestres: 0,16 / 0,40 / 0,41 s.
  - Diferenças dentro da variação da medida.
- **Conferência visual:** árvores, ipês, eucaliptos, palmeiras e arbustos de perto e de longe; mata ao redor do trevo sem invadir a pista; moto e van na rodovia.
- **Atualização simulada da 1.36 para a 1.37:** aplicada pelo atualizador da 1.36, com 21 arquivos novos ou alterados, e o esquema passou a 29.

## Não verificado / limitações
- **Windows e ODA File Converter real:** não testados aqui (testado com um conversor de imitação). Confira:
  - os termos de uso do ODA File Converter para a empresa;
  - se o instalador pede administrador no seu computador.
  - Se puder, mande um DWG de vocês para eu conferir a conversão.
- **Objetos do Civil 3D:** superfícies, alinhamentos e corredores podem chegar só como linhas, ou não chegar. É o mesmo que acontece ao salvar como DXF.
- **Pedestres:** não desviam uns dos outros nem dos veículos (andam nas faixas e caminhos marcados).
- **Plantas avulsas:** o limite é de 20.000; para matas grandes, use áreas.

## Próximas partes (estilo Twinmotion)
- **1.38:** vista inclinada sobre o terreno (MDT).
- **Depois:** modo 3D.
