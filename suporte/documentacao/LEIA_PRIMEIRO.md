# Rodovia Studio 1.39

Aplicativo local com API e interface para produzir apresentações de projetos rodoviários a partir de DXF/KMZ. O pacote inclui o projeto TH57, imagem aérea em cache, configuração e o vídeo aprovado nesta conversa.

## Começar no Windows 64 bits

1. Extraia **todo** o ZIP em uma pasta sua, por exemplo `Documentos\RodoviaStudio`. Não execute de dentro do ZIP.
2. Dê dois cliques em **ABRIR RODOVIA STUDIO** (na primeira vez também é criado o atalho “Rodovia Studio” na Área de Trabalho).
3. Na primeira execução, aguarde o preparo automático de Python, bibliotecas e FFmpeg. É necessária internet nessa etapa. Os arquivos ficam na pasta `runtime`; não é solicitada instalação como administrador.
4. O navegador abre em **http://127.0.0.1:8765**. Mantenha a janela do iniciador aberta durante a geração.
5. Clique **Novo** (ou **Abrir…** para um projeto salvo), envie o DXF e o KMZ/KML e clique **Analisar**: o editor abre sobre a imagem web (Esri) com o DXF simplificado. Os painéis (Projeto, Configuração, Vídeo…) ficam nos ícones à esquerda. **Gerar / atualizar prévia** (painel Vista ou faixa de opções) mostra a imagem do vídeo.

Se a rede da empresa bloquear Python.org, PyPI, downloads ou PowerShell, o preparo dependerá da liberação desses acessos. Uma política corporativa pode bloquear programas portáteis mesmo sem pedido de administrador. O arquivo `instalacao.log` mostra a etapa que falhou. Execute novamente após corrigir a conexão; o iniciador reutiliza os componentes já preparados.

## Novidades 1.3–1.39
- **1.39**: bordas pretas/brancas da imagem local ficam transparentes só no branco 255 / preto 0 ligados à beira da imagem; a imagem começa no primeiro pixel abaixo de 255; branco no meio da imagem não fura mais. Opção “Anterior” mantida. Tráfego: trechos curtos (< 50 m) não entram nas rotas dos veículos (sem ziguezague), com campo para ajustar. Veja ATUALIZACAO_1_39.md.
- **1.38**: correção do instalador do leitor ECW — usa só pacotes prontos (não tenta mais compilar o GDAL), usa o proxy do Windows, baixa os 2 arquivos diretamente quando o índice está bloqueado e, se ainda falhar, mostra uma mensagem clara com os 2 endereços e a pasta `sistema\programa\pacotes_ecw`. Veja ATUALIZACAO_1_38.md.
- **1.37**: abrir DWG (convertido em DXF pelo ODA File Converter instalado no computador); vegetação (árvore, pincel e área: árvore, ipê, eucalipto, palmeira, arbusto, cerca-viva); pedestres em faixas, passarelas e caminhos; frota variada (motos, vans, picapes, carretas). Projetos existentes sem mudança. Veja ATUALIZACAO_1_37.md.
- **1.36**: estilo Twinmotion (parte 1) — câmera por pontos-chave (voo entre vistas marcadas), clima (nublado, chuva com pista molhada, neblina), sombras pela hora do sol e comparação antes/depois no final do vídeo; tudo desligado por padrão. Veja ATUALIZACAO_1_36.md.
- **1.35**: obras do PER (duplicação, via marginal, iluminação e mais 23 tipos) por Excel, cronograma do MS Project (XML) ou início e fim no desenho, com faixa colorida e linha do tempo no vídeo; nome do destaque não some ao trocar a categoria e 18 categorias novas; seleção mais precisa; menus do Windows; tela simplificada. Veja ATUALIZACAO_1_35.md.
- **1.34**: painéis por menu (ícones à esquerda; abrem por cima do desenho ou fixados ao lado; × fecha); visual do Windows 11 com tema claro, escuro ou igual ao Windows; quadro de progresso em vídeo, prévia, exportação e downloads; comandos contínuos (Enter confirma, Esc cancela, o comando segue no próximo objeto); texturas artístico-realistas; tela sem referências a versões anteriores. Veja ATUALIZACAO_1_34.md.
- **1.33**: mais área para o desenho — barra da direita em abas que recolhe e reabre ao editar, abas em janelas flutuantes, área máxima (F10); mensagens, progresso, tempo e Cancelar na barra de status; tempos acima de 60 s em minutos; Gerar vídeo e registros na faixa de opções. Veja ATUALIZACAO_1_33.md.
- **1.32**: pasta principal só com o arquivo principal (auxiliares em “sistema”); vídeos guardados em “videos”, um arquivo por geração; Limpar memória (resíduos); qualidade Alta/Máxima e 4K; atualizar pelo aplicativo. Veja ATUALIZACAO_1_32.md.
- **1.31**: reorganização interna do código (sem funções novas): interface por assunto, servidor por assunto, estilos separados, testes de estrutura e ARQUITETURA.md. O uso continua igual. Veja ATUALIZACAO_1_31.md.
- **1.30**: abrir projeto salvo (lista com miniaturas, Ctrl+O), renomear, modelos de projeto; rotas de veículos com trechos de pista simples, dupla por sentido ou sentido único; painéis com grupos recolhíveis; gerenciador de camadas (visível/oculta/congelada, edição final); pincel de textura até Esc. Veja ATUALIZACAO_1_30.md.
- **1.29**: corrige o erro ao salvar interdições (“partial ou total”); DXF e KMZ/KML enviados na hora; aparência de taludes, canteiro, água e sinalização; faixa de opções no estilo Windows; nomes sempre válidos. Veja ATUALIZACAO_1_29.md.
- **1.28**: alterações feitas durante uma tarefa não se perdem mais; ao concluir um comando a seleção, os grips e a mini-barra somem; o menu do botão direito fecha ao clicar na tela; a prévia à vista é refeita sozinha após as alterações. Veja ATUALIZACAO_1_28.md.
- **1.27**: clique e arraste para mover, alça de giro e mini-barra; clique numa área do desenho e use o botão direito para trocar textura, nome ou tipo; caixa de chamada com linha ajustável; menu do botão direito só com os comandos da seleção; fluxos com ligações, velocidade por trecho e redução nas curvas; velocidade de avanço da apresentação; barra de menus e janela própria do Windows (recompile o .exe). Veja ATUALIZACAO_1_27.md.
- **1.26**: pórticos com a imagem da placa na chamada; caixas de chamada sem sobreposição; ocultar/congelar camadas; hachuras MPOLYGON e por padrão; alinhamento selecionando a linha do desenho; menu do botão direito com ajuda; ATRIB/PINTAR; tela ampla; sessões; registros e prompt para IA. Veja ATUALIZACAO_1_26.md.
- **1.25**: catálogo QuickMapServices — busca os serviços de imagem que cobrem o trecho, testa a nitidez no centro do trecho e aplica o melhor como fonte web (editor, mosaico e aproximação do vídeo). Veja ATUALIZACAO_1_25.md.
- **1.24**: leitor ECW interno que mantém a georreferência; Enter aceita e Esc pede confirmação; seleção por janela/crossing; COPIAR, GIRAR, ESCALA, ESPELHAR, OFFSET; snap exato; informação na tela; menus recolhíveis; seleção de fluxos; texturas editáveis; leitura automática dos hatches do DXF; montagem do vídeo ~20–25 % mais rápida neste ambiente. Veja ATUALIZACAO_1_24.md.
- **1.23**: Rodovia Studio.exe (gerado no seu Windows por COMPILAR INICIADOR.cmd): abre sem janela preta, aplica as atualizações sozinho, fica no ícone perto do relógio; o programa continua em arquivos separados atualizados pelo ZIP. Veja ATUALIZACAO_1_23.md.
- **1.22**: edição tipo CAD — seleção com grips, propriedades com Enter, linha de comando (MOVER, APAGAR, DIST, coordenadas X,Y e @dx,dy), snap e orto, alinhamento por cliques, salvar/salvar como/excluir. Veja ATUALIZACAO_1_22.md.
- **1.21**: pavimento rígido (concreto com juntas a cada 5 m) ou flexível, representação do pavimento escolhida e alterável, vídeo técnico ou artístico, contraste projeto × imagem. Veja ATUALIZACAO_1_21.md.
- **1.20**: veículos em linha reta (sem recuos nas emendas), sentido pelo eixo sem seta, áreas de pista nova/existente/acostamento desenhadas ou selecionadas, acostamento por início/fim/largura, perfil “Apresentação técnica” (hachuras, voo contínuo, progresso), conferência DXF×KMZ e do MP4. Veja ATUALIZACAO_1_20.md.
- **1.19**: Enter encerra o comando; mover pontos (placa, passarela, linha de chamada); imagens locais com prioridade e ajuste por grips; prévia nítida com zoom forte; menus com ícones; limpar trabalho mantendo o segmento; fontes web Esri Wayback/XYZ/WMS; atualizador com caminhos longos. Veja ATUALIZACAO_1_19.md.
- **1.18**: 2 faixas por sentido + acostamento (3ª faixa por início/fim), menos setas, camada 0 separada por cor/tipo, km digitado em planta, vão da passarela no editor e acesso com tapers. Veja ATUALIZACAO_1_18.md.
- **1.17 — imagem local de alta resolução**: ortofoto/drone em GeoTIFF/COG, JPEG2000 ou ECW/MrSID (convertido com o QGIS), em mosaico, no vídeo e no editor. Veja ATUALIZACAO_1_17.md.
- **1.16 — texturas**: asfalto com agregado, pista existente com remendos, fissuras e trilhas de roda, taludes com aparência de terreno (opcional), cor da imagem detalhada ajustada ao mosaico e detalhe a 0,1 m. Veja ATUALIZACAO_1_16.md.
- **1.15 — sinalização completa**: faixas pela largura (ou por trecho), setas por faixa, retenção/PARE, dê a preferência, zebrados, faixas de pedestre, placas e leitura do projeto de sinalização do DXF. Veja ATUALIZACAO_1_15.md.
- **Editor da prévia** (seção 3): zoom, arraste, ferramentas com desfazer/refazer — início do km, intervenção, linha de chamada, OAE por dois pontos, sentido de via, inverter/desativar/incluir fluxo, cruzamento sem conexão, exclusões por vértices ou laço, pares de controle DXF × imagem e cabine. Veja ATUALIZACAO_1_3.md.
- **Camadas, imagem local e intercâmbio**: DXF adicionais, GeoTIFF/arquivo de mundo, GeoJSON, KML/KMZ, DXF, CSV, pacote .zip e sequência PNG. Veja ATUALIZACAO_1_4.md.
- **Qualidade visual** Aprimorada ou Anterior. Veja ATUALIZACAO_1_5.md.
- **Vista da cabine**: ilustrativa; plana sem MDT. Veja ATUALIZACAO_1_6.md.
- **1.7**: editor em tela cheia de verdade (tecla F), geração em vários processos, perfil rápido, elevação do terreno (MDT local ou web) e ficha técnica no lugar do vídeo TH57. Veja ATUALIZACAO_1_7.md.
- **1.8**: botão **Como usar** e dicas **?** em cada campo; estaqueamento automático ou manual (início, fim, sentido, ajuste proporcional); **destaques** com linha de chamada; pasta organizada (projetos, atualizacoes, suporte) e **ATUALIZAR RODOVIA STUDIO**. Veja ATUALIZACAO_1_8.md.
- **1.9**: editor sobre **imagem web Esri** nítida em qualquer zoom, com o **DXF/KMZ simplificado** por cima e camadas liga/desliga; marcações e pares de controle sem depender da prévia; ladrilhos guardados para uso sem internet. Veja ATUALIZACAO_1_9.md.
- **1.10**: vídeo sem sujeiras de sinalização (pintura limpa e ferramenta **Sem sinalização**), setas de fluxo a cada km e nos conflitos, marcos do km inicial/final, seta de sentido no topo, grama nos canteiros, cidades próximas (OpenStreetMap ou manual) e proteções contra entradas degeneradas. Veja ATUALIZACAO_1_10.md.
- **1.11**: ícone e marca GeoRas; editor com fluxos, sentidos e sinalização nítidos logo após a análise (⟳ Atualizar fluxos, sem prévia); imagem web direta pelo navegador; vídeo com imagem Esri ~0,3 m e texturas do projeto a 0,2 m quando a câmera se aproxima; OAE por vértices (polígono irregular) com sentido. Veja ATUALIZACAO_1_11.md.
- **1.12**: sinalização limpa em todo o modelo (bordos pelo contorno do pavimento, rotatórias em arco), seta em todas as faixas, mão de direção nas ilhas; tráfego simulado sem colisão, engarrafamento, interdições de faixa (🚧) com fila e desvio, travessia do canteiro só em retornos ou locais indicados. Veja ATUALIZACAO_1_12.md.
- **1.13**: transição dia → noite (faróis, lanternas e sinalização refletiva em destaque) e duas janelas sincronizadas — configuração numa, visualização e resultados na outra. Veja ATUALIZACAO_1_13.md.
- **1.14**: pronto para outros modelos — tipo de cada camada sempre definido no projeto (nada fixo), perfis de camadas reutilizáveis com curingas, novos tipos (bordo, hidrografia, talude), “Ver” camada no editor, cores por tipo; setas de fluxo giráveis que reorientam o fluxo. Veja ATUALIZACAO_1_14.md.

## Dois resultados disponíveis

- **Ficha técnica de referência (TH57):** dados do vídeo aprovado (2560×1440, 30 fps, 202 s, 6060 quadros, H.264 High, ~18,1 Mbit/s) e métricas de imagem (nitidez, contraste, cor, sinalização e pavimento). O MP4 de 456 MB deixa de ser necessário; **Comparar vídeo gerado com a referência** mostra a tabela lado a lado.
- **Gerar novo vídeo:** executa o motor geométrico deste aplicativo sobre o DXF/KMZ e a configuração atual. Mantém a linguagem visual — satélite, pavimento natural, sinalização, faixa de domínio amarela, identificação fixa, rodapé mínimo, câmera em movimento e veículos — e produz novos quadros. Uma nova renderização não é uma reprodução pixel a pixel da composição histórica, que recebeu revisões de imagem e posicionamento específicas.

O aplicativo entrega as duas funções separadas, identificadas na interface e na API.

## Outros projetos

1. **Novo projeto** → selecione DXF e/ou KMZ → **Enviar arquivos**.
2. Informe o CRS projetado correto, o fator de unidade para metros, quilômetros inicial/final, extensão de referência, origem/destino e ano.
3. **Analisar arquivos**. Abra **Camadas e sentidos de circulação** e confira as associações. Camadas com nomes diferentes podem ser associadas manualmente.
4. **Salvar configuração** → **Gerar / atualizar prévia**. Confira alinhamento, início/fim do eixo e a correspondência com a imagem aérea. Se necessário, inverta o eixo e ajuste o CRS.
5. Para incluir OAE, passarela, marginal, correção, interseção ou fauna, selecione **Posicionar intervenção**, clique na prévia, preencha o nome e clique **Adicionar intervenção**. Edite o km de cada ponto quando houver referência oficial.
6. Selecione **Marcar área de limpeza**, clique nos vértices e depois **Concluir área**. A limpeza remove corte/aterro e bloqueia veículos dentro da região; não apaga pavimento ou faixa de domínio. **Desfazer área** remove o último vértice ou a última região.
7. Salve e atualize a prévia. Marque a confirmação de coordenadas e gere o vídeo.
8. Acompanhe a tarefa e clique **Baixar MP4**. Configurações e resultados ficam na pasta `dados` e podem ser reabertos na lista de projetos.

A prévia pode mostrar **Vista geral** ou a **Câmera do vídeo** no instante escolhido. Use a segunda opção para conferir o pavimento e as intervenções de perto.

**Esri online** baixa e reutiliza mosaicos para o novo trecho. **Cache TH57** funciona para a área do exemplo. **Fundo neutro** permite testar a geometria sem imagem aérea. A fonte da imagem aparece no cabeçalho. Uma falha da base online é apresentada como erro; o aplicativo não troca silenciosamente por um fundo fictício.

## Geometria e circulação

- Lê blocos inseridos e curvas DXF com subdivisão adaptativa; preserva os contornos e ilhas de hachuras.
- A faixa de domínio vem das entidades nativas, sem ser inventada por afastamento do eixo.
- A extensão contratual e o comprimento geométrico são campos distintos. O vídeo exibe a extensão de referência.
- O sentido principal é definido pelo início do eixo e pela posição relativa das pistas. É possível ajustar cada eixo em direto, inverso ou sem veículos. O modo automático é uma sugestão e precisa ser conferido para cada novo projeto.
- Veículos seguem trajetórias fixas sobre os eixos existentes, com verificação do retângulo do veículo no pavimento permitido. Não há mudança aleatória de faixa.
- Ramais e marginais precisam de eixos desenhados e corretamente associados. A aplicação não inventa acessos ausentes. Os fluxos são ilustrativos, sem simulação de demanda, preferência de passagem ou certificação de sinalização.
- Passarelas adicionadas como intervenção recebem representação esquemática em planta; o dimensionamento estrutural não é inferido.
- CRS ausente/incorreto, eixo com sentido invertido ou camadas associadas incorretamente precisam ser corrigidos na etapa de configuração. A análise apresenta alertas, não substitui conferência de engenharia.

## Aceleração e cache

Na etapa 5, selecione Automática para testar NVIDIA NVENC. Se indisponível, a CPU é utilizada. O teste físico é feito no próprio computador. O perfil CPU pode ser fast (original) ou veryfast (mais rápido). A montagem das imagens segue na CPU. Consulte ATUALIZACAO_1_1.md para parâmetros, medição e testes.

## Vídeo

Para 1440p com mosaico de 8192 pixels, recomenda-se computador de 64 bits com 16 GB de RAM e espaço livre para o vídeo. Use 720p e mosaico menor para testes rápidos. O cache TH57 incluído possui 8192 pixels.


1280×720, 1920×1080 ou 2560×1440; 24 ou 30 fps; duração configurável de 3 a 1800 s; H.264 High, yuv420p, CRF 16, limite de 18 Mbit/s com buffer de 36 Mbit, keyint 250, faststart. A duração é arredondada ao número inteiro de quadros mais próximo. O padrão é 202 s e 30 fps, totalizando 6060 quadros.

As chamadas ocupam uma posição fixa no cabeçalho; os pequenos símbolos geográficos acompanham o mapa. O rodapé exibe km inicial, km final, extensão e ano. A câmera percorre o eixo e visita até onze intervenções em cenas de detalhe. A trajetória de novos projetos é calculada a partir de seus próprios dados.

## API local

Documentação interativa em **http://127.0.0.1:8765/docs**.

| Método | Rota | Função |
|---|---|---|
| POST | `/api/projects` | Criar projeto com configuração JSON |
| POST | `/api/example` | Carregar exemplo TH57 |
| POST | `/api/projects/{id}/files` | Upload multipart `file`, DXF ou KMZ |
| PUT | `/api/projects/{id}/config` | Salvar configuração validada |
| POST | `/api/projects/{id}/analyze` | Enfileirar análise |
| POST | `/api/projects/{id}/preview` | Enfileirar prévia |
| POST | `/api/projects/{id}/render` | Enfileirar nova renderização |
| POST | `/api/projects/{id}/reference` | Exportar cópia do vídeo TH57 aprovado |
| GET | `/api/jobs/{id}` | Estado, etapa, progresso e erro |
| POST | `/api/jobs/{id}/cancel` | Solicitar cancelamento |
| GET | `/api/projects/{id}/video.mp4` | Baixar resultado |
| GET | `/api/projects/{id}/config.json` | Baixar configuração |

As tarefas usam processos separados e fila persistida em SQLite. O navegador pode fechar enquanto a aplicação continua aberta. Encerrar o iniciador interrompe a renderização; ao reiniciar, a tarefa é identificada como interrompida e pode ser iniciada novamente. O aplicativo processa uma tarefa por vez. Não o exponha na internet: o servidor foi configurado exclusivamente para uso local.

## Instalação manual / Linux

Python 3.12 de 64 bits:

```bash
python -m venv .venv
# Ative o ambiente de acordo com seu sistema.
python -m pip install -r requirements.txt
python diagnostico.py
python run.py
```

Em Linux/macOS também pode usar `sh iniciar.sh`. O iniciador de Windows não foi executado neste ambiente Linux; os testes funcionais da API e do renderizador foram executados conforme `RELATORIO_DE_TESTES.md`.

## Fontes e manutenção

- Organização da pasta: `ABRIR RODOVIA STUDIO.cmd`, `ATUALIZAR RODOVIA STUDIO.cmd`, `projetos/`, `atualizacoes/` e `suporte/` (`sistema`, `documentacao`, `backups`, `logs`).
- `suporte/sistema/app/`: API, interface e motor.
- `assets/th57/`: desenho, cache de imagem, configuração e ficha técnica do vídeo aprovado (`referencia_ficha.json`).
- `assets/fonts/`: fontes e licença.
- `tests/`: testes automatizados. Para executá-los: instale `requirements-dev.txt` e rode `python -m pytest -q` na pasta do aplicativo.
- `dados/`: projetos do usuário, criados durante o uso.

Não há chave de IA nem serviço de renderização pago necessário. O programa usa processamento geométrico local. O cache de imagens e a configuração podem ser reutilizados sem chamadas de IA.

## Documentação dos componentes

- FastAPI: https://fastapi.tiangolo.com/
- ezdxf: https://ezdxf.readthedocs.io/
- imageio-ffmpeg: https://github.com/imageio/imageio-ffmpeg
- Python portátil: https://www.python.org/downloads/release/python-31210/
