# Inventário nominal da interface 1.42.36

Este documento complementa ANALISE.md. Instâncias, aliases, modos e comandos não devem ser somados como funções únicas. Campos, handlers e controles ocultos estão integralmente nos CSVs/JSONs. Diálogos dinâmicos dependem de contexto e foram analisados também pelo código.

## Menus e submenus reais

### Arquivo

- Novo projeto
- Novo a partir de modelo…
- Abrir projeto…Ctrl+O
- SalvarCtrl+S
- Salvar como…
- Histórico e recuperação…
- Renomear projeto…
- Salvar como modelo…
- Modelos de projeto…
- Exportar e importar…
- Registros e suporte
- Baixar registros (.zip)
- Detalhes do último erro
- Prompt para IA
- Excluir projeto…
- Vídeos gerados…
- Limpar memória (resíduos)…
- Atualizar o Rodovia Studio…

### Editar

- DesfazerCtrl+Z
- RefazerCtrl+Y
- Mover
- Girar
- Copiar
- Escala
- Espelhar
- Offset
- Apagar
- Propriedades ›
  - Seleção ›
    - Selecionar tudo
    - Desmarcar
    - Propriedades
  - Modificar ›
    - Mover
    - Girar
    - Copiar
    - Escala
    - Espelhar
    - Paralela
  - Aparência ›
    - Textura
    - Pincel
    - Gerenciador de camadas
  - Histórico ›
    - Desfazer
    - Refazer
    - Apagar
- Outras ferramentas ›
  - Vão da passarela
  - Linha de chamada
  - Trecho da rota
  - Obra do PER
  - Caminho de pedestres
  - Cabine
  - Inserir vértice
  - Apagar intervalo do fluxo
  - Juntar subsegmentos
  - Inserir nó de ligação
  - Selecionar nó
  - Editar nó
  - Mover nó de ligação
  - Apagar nó
  - Nó de entrada, saída ou fim
  - Inspecionar arrasto dos veículos

### Projeto

- Proteção e recuperação de dados
- Analisar layers e eixos / IA
- Projeto ›
  - Novo
  - Abrir…
  - Salvar
  - Salvar como…
- Arquivos ›
  - DXF/DWG…
  - KMZ/KML…
  - Analisar
- Dados ›
  - Configuração
  - Camadas
  - Obras do PER
- Traçado e referências ›
  - Alinhamento (cliques)
  - Rota de veículos
  - Início do km
  - Fim do km
  - Par de controle
  - Ajustar imagem local

### Tráfego

- Regras e operação dos fluxos
- Criar ligação de ramal
- Diagnosticar veículos
- IA assistida de execução
- Escolher eixo e configurar faixas
- Gerar e visualizar
- Corrigir problemas
- Tráfego e ligações ›
  - Selecionar e editar fluxos
  - Incluir fluxo
  - Inverter fluxo
  - Desativar fluxo
  - Forçar ligação
  - Sem conexão (ponto)
  - Sem conexão (área)
  - Sentido
  - Girar seta
  - Faixas por trecho
  - 3ª faixa (início/fim)
  - Interdição
  - Travessia permitida
  - Travessia proibida
- Ferrovia e semáforos ›
  - Ferrovia
  - Semáforo
  - Link de onda verde

### Cena

- Pavimento e superfícies ›
  - Área de pista (desenhar)
  - Área de pista (selecionar)
  - Acostamento (início/fim)
  - Pincel de textura
  - Zebrado
  - Sem sinalização
  - Exclusão (vértices)
  - Exclusão (laço)
  - Editar vértices
- Sinalização e estruturas ›
  - Placa
  - Faixa de pedestre
  - Pórtico
  - OAE (2 pontos)
  - OAE (vértices)
  - Acesso com taper
- Apresentação e ambiente ›
  - Destaque
  - Intervenção
  - Cidade
  - Velocidade de avanço (trecho)
  - Vegetação
- Materiais e texturas

### Vídeo

- Produção ›
  - Configurar
  - Prévia no instante
  - Gerar vídeo
- Câmera e ambiente ›
  - Ponto-chave
  - Clima e sol
- Resultados ›
  - Vídeos gerados
  - Registros

### Exibir

- Área de trabalho ›
  - Modo Projeto
  - Projeto
  - Propriedades
  - Linha de comando
- Vista ›
  - Enquadrar
  - Regenerar
  - Tela cheia
  - Snap
  - Orto
- Vista 3D ›
  - Vista 3D / editor 2D

### Ajuda

- IA de apoio — API online
- Diagnóstico dos logs / IA
- Ajuda ›
  - Como usar
  - Comandos
  - Sobre

## Abas e botões encontrados no painel ativo

### Projeto

- Analisar layers / IA
- Arquivos do projeto
- Camadas e imagens
- Par de controle
- Alinhamento (cliques)
- Cabine
- Recolher ferramentas
- Localizar defeitos, recuperar partes válidas, recortar e revisar camadas
- Orientação dos cálculos
- Configurar imagens…
- Recolher ferramentas
- Proteção de dados
- Conectar API online ou consultar modelo local com mini prompts revisáveis

### Editar

- Mover
- Girar
- Copiar
- Escala
- Espelhar
- Paralela
- Apagar
- Mover ponto
- Inserir vértice
- Editar vértices
- Ajustar imagem local
- Medir distância
- Calcular e atualizar fluxos
- Inspecionar
- Início do km
- Fim do km
- Intervenção
- Vão da passarela
- Linha de chamada
- Destaque
- OAE (2 pontos)
- OAE (vértices)
- Cidade
- Pórtico
- Obra do PER
- Recolher ferramentas

### Tráfego

- Testar circulação
- Sentidos e nós
- Inserir nó de ligação
- Selecionar nó
- Editar nó
- Mover nó de ligação
- Apagar nó
- Nó de entrada, saída ou fim
- Inspecionar arrasto dos veículos
- Modo clássico de fluxo
- Escolher eixo
- Configurar faixas
- Corrigir problemas
- Selecionar e editar fluxos
- Rota de veículos
- Trecho da rota
- Girar seta
- Sentido
- Inverter fluxo
- Desativar fluxo
- Incluir fluxo
- Forçar ligação
- Sem conexão (ponto)
- Sem conexão (área)
- Apagar intervalo do fluxo
- Juntar subsegmentos
- Seção típica de fluxo — escolher eixo, faixas e acostamentos
- 3ª faixa (início/fim)
- Faixas por trecho
- Interdição
- Acesso com taper
- Travessia permitida
- Travessia proibida
- Velocidade de avanço (trecho)
- Ferrovia
- Semáforo
- Link de onda verde
- Recolher ferramentas
- IA assistida de fluxos
- Controles individuais, entrada de 5 m, distribuição e eixos sem pavimento
- Diagnosticar veículos
- Gerar e visualizar
- Recolher opções

### Cena

- Materiais e texturas
- Vista 3D
- Exclusão (vértices)
- Exclusão (laço)
- Sem sinalização
- Zebrado
- Faixa de pedestre
- Placa
- Área de pista (desenhar)
- Área de pista (selecionar)
- Acostamento (início/fim)
- Pincel de textura
- Materiais, símbolos e nomes CAD
- Contornos e máscaras da imagem aérea
- Vegetação
- Caminho de pedestres
- Recolher ferramentas
- Reproduzir tráfego
- Pausar tráfego
- Seguir veículo
- Enquadrar 3D
- Planta 3D
- Iluminação
- Diagnósticos técnicos
- Reconstruir 3D
- Capturar imagem 3D
- Exportar prévia 3D MP4
- Voltar ao editor 2D

### Vídeo

- Conferir por que não há veículos e gerar uma prévia em detalhe
- Configurar vídeo
- Gerar prévia
- Gerar vídeo
- Vídeos gerados
- Registros da exportação
- Prompt de reprodução
- Recolher ferramentas

## Ferramentas-base e extensões: decisão individual

| ID | Ferramenta | Encaminhamento |
|---|---|---|
| pan | ✋ Navegar / selecionar | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| move | ✥ Mover ponto | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| imgadjust | ⧉ Ajustar imagem local | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| inspect | ⌖ Inspecionar | Complementar ao diagnóstico: inspeção não é correção nem autorização. |
| align | ⟋ Alinhamento (cliques) | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| chain | 📏 Início do km | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| chainend | 🏁 Fim do km | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| poi | 📍 Intervenção | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| span | ↔ Vão da passarela | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| anchor | ↘ Linha de chamada | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| highlight | ⭐ Destaque | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| oae | 🌉 OAE (2 pontos) | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| oaepoly | 🌉 OAE (vértices) | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| arrowrot | ↻ Girar seta | Preservar escopo; distinguir sentido da via, override local e seta. |
| dir | ➜ Sentido | Preservar escopo; distinguir sentido da via, override local e seta. |
| route | 🛣 Rota de veículos | Consolidar entrada em seção típica; migrar/prever precedência de contratos legados. |
| routesec | ⇶ Trecho da rota | Consolidar entrada em seção típica; migrar/prever precedência de contratos legados. |
| obra | 🏗 Obra do PER | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| veg | 🌳 Vegetação | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| pedestres | 🚶 Caminho de pedestres | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| linkforce | ⤳ Forçar ligação | Consolidar criação no editor de nós; manter vínculo de origem e confirmação. |
| flowrev | ⇄ Inverter fluxo | Preservar escopo; distinguir sentido da via, override local e seta. |
| flowoff | ⦸ Desativar fluxo | Manter em edição avançada de tráfego; exclusão e junção não são equivalentes. |
| flowadd | ✚ Incluir fluxo | Manter em edição avançada de tráfego; exclusão e junção não são equivalentes. |
| noconn | ✕ Sem conexão (ponto) | Manter restrição específica; não fundir com exclusão visual ou desligamento. |
| noconnarea | ⬚ Sem conexão (área) | Manter restrição específica; não fundir com exclusão visual ou desligamento. |
| exvert | ⬠ Exclusão (vértices) | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| exlasso | ✎ Exclusão (laço) | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| exedit | ◇ Editar vértices | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| cleanarea | 🧽 Sem sinalização | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| hatch | ▨ Zebrado | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| crosswalk | 🚶 Faixa de pedestre | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| sign | 🛑 Placa | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| gantry | ⊓ Pórtico | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| advzone | ⏱ Velocidade de avanço (trecho) | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| pavarea | ▦ Área de pista (desenhar) | Compartilhar editor contextual de superfícies/material; manter modo de seleção/desenho. |
| pavpick | ⬚ Área de pista (selecionar) | Compartilhar editor contextual de superfícies/material; manter modo de seleção/desenho. |
| shoulder | ⇥ Acostamento (início/fim) | Compartilhar editor contextual de superfícies/material; manter modo de seleção/desenho. |
| lanerange | ➕ 3ª faixa (início/fim) | Consolidar entrada em seção típica; migrar/prever precedência de contratos legados. |
| lanes | ☰ Faixas por trecho | Consolidar entrada em seção típica; migrar/prever precedência de contratos legados. |
| city | 🏙 Cidade | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| block | 🚧 Interdição | Manter restrição específica; não fundir com exclusão visual ou desligamento. |
| access | 🛣 Acesso com taper | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| crossok | ↶ Travessia permitida | Manter restrição específica; não fundir com exclusão visual ou desligamento. |
| crossno | ⛔ Travessia proibida | Manter restrição específica; não fundir com exclusão visual ou desligamento. |
| pair | ⊕ Par de controle | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| cabin | 🚗 Cabine | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| brush | 🖌 Pincel de textura | Compartilhar editor contextual de superfícies/material; manter modo de seleção/desenho. |
| insertcontrol | Inserir vértice | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| railway | Ferrovia | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| traffic_signal | Semáforo | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| signal_link | Link de onda verde | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| flowcut | Apagar intervalo do fluxo | Manter em edição avançada de tráfego; exclusão e junção não são equivalentes. |
| flowjoin | Juntar subsegmentos | Manter em edição avançada de tráfego; exclusão e junção não são equivalentes. |
| sectionpoint | Limite da seção | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| imagesample | Amostra da imagem | Preservar função específica; delegar acessos ao mesmo registro de comando. |
| nodeadd | Inserir nó de ligação | Consolidar criação no editor de nós; manter vínculo de origem e confirmação. |
| nodeselect | Selecionar nó | Preservar ação específica em grupo Nós; reutilizar formulário e estado. |
| nodeedit | Editar nó | Preservar ação específica em grupo Nós; reutilizar formulário e estado. |
| nodemove | Mover nó de ligação | Preservar ação específica em grupo Nós; reutilizar formulário e estado. |
| nodedelete | Apagar nó | Preservar ação específica em grupo Nós; reutilizar formulário e estado. |
| nodeend | Nó de entrada, saída ou fim | Preservar ação específica em grupo Nós; reutilizar formulário e estado. |
| swept | Inspecionar arrasto dos veículos | Complementar ao diagnóstico: inspeção não é correção nem autorização. |

## Seções recolhíveis e subabas do DOM carregado

| Seção | Grupo pai | Subaba/seção |
|---|---|---|
|  |  | Diagnóstico |
|  |  | Mais ferramentas |
|  |  | Parâmetros de apresentação |
|  |  | Mais ferramentas |
|  |  | Mais ferramentas |
|  |  | Mais opções |
|  |  | Mais ferramentas |
|  |  | Mais ferramentas |
|  |  | Resultado do vídeo |
| 2. Configuração |  | Fonte da imagem web (Esri atual, Esri Wayback por data, outro serviço) |
| 2. Configuração |  | Hachuras do DXF (leitura automática) |
| 2. Configuração |  | Camadas e sentidos de circulação |
| 2. Configuração | Camadas e sentidos de circulação | Cores por tipo |
| Camadas, imagem local e intercâmbio |  | Camadas DXF adicionais |
| Camadas, imagem local e intercâmbio |  | Imagem georreferenciada local (ortofoto, drone, ECW) |
| Camadas, imagem local e intercâmbio |  | Elevação do terreno (MDT) |
| Camadas, imagem local e intercâmbio |  | Exportar e importar |
| 5. Exportar vídeo |  | Câmera, clima, sol, vida e antes/depois |
| 5. Exportar vídeo |  | Vista da cabine (primeira pessoa) |
| 5. Exportar vídeo |  | Tráfego: simulação, engarrafamento e canteiro |
| 5. Exportar vídeo |  | Perfil de apresentação, veículos e sentido |
| 5. Exportar vídeo |  | Dia e noite |
| 5. Exportar vídeo |  | Sinalização, setas e anotações do vídeo |
| 5. Exportar vídeo |  | Ficha técnica de referência e comparação e comparação |
| 4. Intervenções e identificações |  | Passarelas e baias — dimensões esquemáticas em metros |
| Vista, prévia e sessões |  | Camadas |
| 3. Editor (imagem web ou prévia) |  | Marcações do projeto |
| 3. Editor (imagem web ou prévia) |  | Ajuste DXF × imagem |
| 3. Editor (imagem web ou prévia) |  | Conexões de tráfego (fluxos desenhados) |
|  |  | Configurações de vídeo e tráfego |

## Comandos registrados e aliases

Cada alias conserva o mesmo handler exibido no CSV; comandos CAD interpretados por runCommand são complementares ao registro COMANDOS.

`ABRIR`, `OPEN`, `MODELOS`, `MODELO`, `TEMPLATE`, `RENOMEAR`, `REN`, `ROTA`, `RT`, `ROUTE`, `TRECHO`, `TR`, `CAMADAS`, `LA`, `LAYER`, `GERENCIADOR`, `PINCEL`, `PI`, `BRUSH`, `VIDEOS`, `VID`, `LIMPAR`, `LIMPEZA`, `ATUALIZAR`, `VERSAOANTERIOR`, `ROLLBACK`, `AREA`, `MAX`, `AREAMAX`, `VIDEO`, `GERAR`, `PAINEIS`, `PNL`, `TEMA`, `OBRA`, `PER`, `CRONOGRAMA`, `IMPORTAROBRAS`, `CAMERA`, `PC`, `ARVORE`, `VEGETACAO`, `VEG`, `PEDESTRES`, `CAMINHO`, `COMANDO`, `CMD`, `FOCO`, `PROJETO`, `EDITARFLUXOS`, `REDRAW`, `CALCULARFLUXOS`, `FERROVIA`, `SEMAFORO`, `ONDAVERDE`, `MATERIAIS`, `NOMESCAD`, `SECOESTIPO`, `PARESIGA`, `IMAGEMCONTORNOS`, `CORRIGIRFLUXOS`, `ASSISTENTEIA`, `ANALISARCAMADAS`, `PROTEGERPROJETO`, `IAFLUXOS`, `IA3B`, `DIAGNOSTICARVEICULOS`, `REGRASFLUXO`, `RAMAIS`, `INSERIRNO`, `EDITARNO`, `APAGARNO`, `MOVERNO`, `ARRASTO`, `FLUXOCLASSICO`, `SENTIDOS`, `REVERSAO`, `TESTARCIRCULACAO`

## Fontes principais

Os caminhos abaixo são relativos à raiz do repositório. Linhas iniciais dos módulos indicam os grupos estudados; os arquivos de referências guardam linha e conteúdo individual.

- [53_interface_estudos.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/53_interface_estudos.js:1)
- [51_shell_profissional.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/51_shell_profissional.js:1)
- [75_operacao_consolidada.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/75_operacao_consolidada.js:1)
- [76_politica_atualizacao.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/76_politica_atualizacao.js:1)
- [59_paineis_destacados.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/59_paineis_destacados.js:1)
- [64_janelas_modelagem.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/64_janelas_modelagem.js:1)
- [65_secoes_pare_siga.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/65_secoes_pare_siga.js:1)
- [70_correcao_fluxos.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/70_correcao_fluxos.js:1)
- [79_execucao_protecao.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/79_execucao_protecao.js:1)
- [84_diagnostico_veiculos.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/84_diagnostico_veiculos.js:1)
- [85_operacao_fluxos.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/85_operacao_fluxos.js:1)
- [86_nos_arrasto.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/86_nos_arrasto.js:1)
- [87_circulacao_simples.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/87_circulacao_simples.js:1)
- [63_catalogo_materiais.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/63_catalogo_materiais.js:1)
- [77_assistencia_ia.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/77_assistencia_ia.js:1)
- [80_cad_compacto.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/80_cad_compacto.js:1)
- [82_diagnostico_video.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/82_diagnostico_video.js:1)
- [83_ia_pequena.js](/workspace/videosRodoviarios/rodovia_studio/pacote/suporte/sistema/app/js/83_ia_pequena.js:1)
