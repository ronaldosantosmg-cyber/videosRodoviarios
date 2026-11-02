# Rodovia Studio 1.3 — Fase A: editor interativo e circulação

## O que mudou

**Editor da prévia (seção 3).** A imagem da prévia virou um editor: roda do mouse aproxima no ponto do cursor, arrastar move (ferramenta Navegar, botão do meio ou espaço + arraste), **Ajustar** encaixa na tela e **Tela cheia** amplia o editor. A régua **Instante da câmera do vídeo** + **Abrir neste instante** gera a prévia em qualquer instante da câmera; **Detalhar vista atual** renderiza em alta resolução o enquadramento do editor. A barra de ferramentas destaca a ferramenta ativa e mostra a instrução dela. Sob o cursor aparecem X, Y, CRS, km e distância ao eixo.

**Desfazer/refazer** (botões ou Ctrl+Z / Ctrl+Y) cobre todas as marcações. A lista **Marcações do projeto** permite editar (nome, nível, km manual, raio, ativo) e excluir cada item, e **Ver** centraliza o item. As alterações são gravadas automaticamente na configuração do projeto, em coordenadas do CRS; nada é escrito no DXF.

| Ferramenta | Função |
|---|---|
| Início do km | Clique sobre o eixo: ali vale o km inicial. km de qualquer ponto = km inicial + distância percorrida ao longo do eixo a partir desse ponto (pontos antes dele recebem km menor). |
| Intervenção | Preenche X/Y do formulário da seção 4. O km pode ser **Calculado pelo estaqueamento** ou **Manual (referência oficial)**. |
| Linha de chamada | Define, move (arrastando) e exclui o ponto de ancoragem da caixa de cada obra. Sem ponto, vale o comportamento automático da 1.2. |
| OAE (2 pontos) | Início e fim sobre o eixo. Cria a OAE com nome, km inicial/final calculados (com opção manual), nível e largura; tem tabuleiro, guarda-corpos e sombra próprios e entra no grafo como estrutura (sem conexões em planta). |
| Sentido | Clique e arraste sobre a pista. A seta vale para o trecho mais próximo e tem prioridade sobre o fluxo do eixo e sobre a sugestão automática. O editor mostra setas de sentido em todas as trajetórias. |
| Inverter fluxo | Clique numa trajetória: inverte os veículos daquele trecho. Clicar de novo desfaz. |
| Desativar fluxo | Clique numa trajetória: ela sai dos itinerários, mas a geometria fica (tracejada). Clicar de novo reativa. |
| Incluir fluxo | Polilinha validada pela mesma regra do motor. Se for rejeitada, a mensagem diz o motivo (fora do pavimento, atravessa canteiro/barreira, área de exclusão, veículo não cabe) e o ponto do problema aparece em vermelho. |
| Sem conexão (ponto/área) | Cruzamento em desnível marcado pelo usuário: dentro dele o grafo não cria ligações nem cortes; os veículos seguem na própria via. Complementa a detecção automática da 1.2. |
| Exclusão (vértices / laço) | Contorno por cliques ou à mão livre (simplificado). **Editar vértices**: arrastar move, clicar na aresta insere, Shift+clique remove. Regra mantida: remove corte/aterro e veículos; preserva pavimento e faixa de domínio. |
| Par de controle | Ponto no DXF → mesmo ponto na imagem. Modelos **Translação** (1 par) ou **Similaridade** (translação + rotação + escala, 2 pares ou mais). Mostra o resíduo de cada par em metros e o RMS; pares podem ser desligados ou excluídos; **Aplicar ao DXF** e **Reverter**. O ajuste é aplicado em memória na leitura. |

**Configuração.** Esquema com `schema_version` e migração automática ao abrir projetos antigos. Na migração, intervenções com km digitado ficam com km manual (mesmo resultado da 1.2) e textos gravados com codificação errada são reparados.

**Correção encontrada no seu computador.** O exemplo TH57 era lido sem UTF-8 no Windows, e por isso os títulos apareciam como “OAE â€¢ Passagem de fauna”. Agora a leitura é explícita em UTF-8, e a migração repara as configurações que já tinham sido gravadas com o erro.

**Robustez local.**
- Trocas de arquivo (vídeo, prévia, JSON) agora tentam de novo por alguns segundos quando o OneDrive, o antivírus ou um player está segurando o arquivo.
- Erros que derrubam o processo de geração ficam em `worker.log` do projeto.
- O `run.py` reconhece um Rodovia Studio já aberto e escolhe outra porta se a 8765 estiver ocupada por outro programa. Falhas de inicialização ficam em `servidor_erro.log`.
- O `iniciar.ps1` instala sem internet quando existe a pasta `pacotes` com os .whl.

## Medido
- Mesmo projeto TH57 em 1280×720, quadros 0–96 s (2881 quadros sequenciais), sem marcações: quadros 14, 40 e 96 s **idênticos pixel a pixel** aos da 1.2; tempo 157,4 ms/quadro (1.2) × 158,1 ms/quadro (1.3).
- Testes automatizados da fase: persistência via API, migração da 1.2, km em eixo curvo, km com eixo invertido, inversão/inclusão/remoção de fluxo, rejeição com motivo, bloqueio em cruzamento sem conexão, OAE por dois pontos, chamada salva/desenhada/excluída, ajuste com resíduos conhecidos, editor e validação após a prévia.
- Teste de interface em Chromium (Playwright): zoom, início do km, desfazer/refazer, seta, exclusão por vértices e por laço, edição de vértice, inverter/desativar fluxo, OAE, cruzamento, fluxo rejeitado e aceito, par de controle, exclusão pela lista e gravação automática conferida pela API. Nenhum erro de JavaScript.

## Não testado / limites
- Interface não testada no Edge/Chrome do Windows; o teste usou Chromium no Linux.
- Os vínculos de seta, inversão e desativação são pela trajetória mais próxima (até 6 m). Se as camadas ou o eixo mudarem muito, confira as marcações na prévia.
- “Sem conexão” não cria viaduto nem altera cotas: só impede ligações no grafo.
