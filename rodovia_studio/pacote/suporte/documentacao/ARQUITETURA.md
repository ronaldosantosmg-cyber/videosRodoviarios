# Rodovia Studio — arquitetura do código (1.31, atualizado na 1.34)

Este guia é para quem mantém o programa: onde fica cada coisa e como acrescentar uma função sem remendar o que já existe.

## Pastas da instalação (1.32)

| Pasta/arquivo | Conteúdo |
|---|---|
| `Rodovia Studio.exe` ou `ABRIR RODOVIA STUDIO.cmd` | o único arquivo da pasta principal |
| `projetos/` | projetos (`store.ROOT`) |
| `videos/<projeto>/` | um MP4 + ficha JSON por geração (`store.videos_root()`, `app/videos.py`) |
| `atualizacoes/` | ZIPs de atualização |
| `sistema/programa/` | o programa (antes `suporte/sistema`): `app`, `runtime`, `run.py`, `atualizador.py`… |
| `sistema/documentacao`, `sistema/backups`, `sistema/logs` | documentação, cópias das atualizações, registros |
| `sistema/*.cmd`, `sistema/LEIA-ME.txt` | atualizar, compilar o .exe, abrir (reserva) e instruções |

O formato do ZIP de atualização não mudou (`pacote/raiz`, `pacote/suporte/...`); o `atualizador.py` traduz para as pastas acima e reorganiza instalações antigas. `run.py` arruma a pasta principal a cada abertura (`atualizador.organize_root`).

## Visão geral

| Parte | Onde | O que faz |
|---|---|---|
| Servidor local | `app/server.py` | Cria o aplicativo FastAPI, o despachante de tarefas (um processo `app.worker` por tarefa), a segurança (só `localhost`) e o tratamento de erros. Nada de rotas aqui. |
| Rotas da API | `app/rotas/<assunto>.py` | Uma `APIRouter` por assunto. `comum.py` tem a fila de tarefas (`idle`, `enqueue`), a configuração (`_config`, `_save_config`) e os arquivos enviados. |
| Modelo de dados | `app/models.py`, `app/migration.py` | Configuração do projeto (pydantic) e migração automática de versões antigas (`SCHEMA_VERSION`). |
| Geração do vídeo | `app/render.py`, `visual.py`, `detail.py`, `geometry.py`, `traffic.py`, `simulation.py`, `routes.py`, `signage.py` … | Cena, quadros, rede de tráfego, rotas de veículos, sinalização. |
| Tarefas em segundo plano | `app/worker.py` | Análise, prévia, vídeo e exportações (processo separado). |
| Interface | `app/index.html`, `app/estilo.css`, `app/js/NN_assunto.js` | Página, estilos (com variáveis de cor em `:root`) e scripts. |
| Ajuda | `app/ajuda.html` | “Como usar”. |

## Rotas da API (`app/rotas`)

| Arquivo | Assunto |
|---|---|
| `paginas.py` | página, ajuda, `/app.js`, `/estilo.css`, ícones, saúde, Sobre |
| `projetos.py` | criar, listar, abrir, renomear, salvar como, retirar, configuração, pacote, importação |
| `modelos.py` | modelos (templates) de projeto |
| `editor.py` | vetores, snap, seleção de linhas/áreas, alinhamento, rotas, texturas, esquema |
| `tarefas.py` | análise, prévia, vídeo, exportações, cancelar, resultados |
| `arquivos.py` | DXF/KMZ, imagens das chamadas, camadas extras, imagem local, ECW, elevação |
| `web.py` | ladrilhos Esri, Wayback, fonte do projeto, QuickMapServices |
| `suporte.py` | sessões e registros (execução, erros, prompt para IA) |
| `videos.py` | vídeos guardados, abrir pastas no Explorer, limpeza de resíduos (`app/maintenance.py`) |
| `sistema.py` | atualização pelo próprio aplicativo |
| `camadas.py` | perfis de camadas e prévia por camada |

Para uma rota nova: escolha o arquivo do assunto (ou crie um e inclua-o na lista do fim de `server.py`) e use `@router.get/post/...`. Funções comuns ficam em `comum.py`.

## Interface (`app/js`)

O navegador recebe **um script só** (`/app.js`), montado na ordem dos números dos arquivos (`00_nucleo.js` … `99_registros.js`). Cada parte começa com `// ==== arquivo: NN_assunto.js ====`, o que ajuda a localizar a linha de um erro. O comportamento é o mesmo de quando tudo estava num arquivo.

| Faixa | Conteúdo |
|---|---|
| `00` | núcleo: `estender`, registros (`ferramenta`, `comando`, `itemFaixa`, `itemArquivo`), utilidades (`$`, `api`, `msg`…) |
| `01–13` | estado das marcações e desfazer, configuração, vista, imagem web, geometria/km, ferramentas, desenho, listas, tarefas, camadas, imagem local, cabine, ajuda, janelas, pavimento |
| `14–18` | edição tipo CAD, hachuras, confirmação e menus, transformações e snap, QuickMapServices |
| `19–27` | pórticos e chamadas, camadas ocultas/congeladas, alinhamento e comandos, menu de contexto, sessões e registros, edição direta, fluxos, menus/status, comandos limpos |
| `28–30` | opções válidas e nomes, arquivos do projeto e aparência, faixa de opções |
| `31–35` | projetos e modelos, rotas de veículos, painéis recolhíveis, gerenciador de camadas, pincel |
| `36` | qualidade do vídeo, vídeos gerados, limpar memória, atualizar pelo aplicativo |
| `37` | janelas no padrão do Windows (título com ×, conteúdo com rolagem, rodapé fixo) |
| `38` | área de trabalho (1.33): barra da direita em abas (`montarDock`, `abrirAba`, `recolherDock`), janelas flutuantes (`destacar`, `encaixar`), área máxima (`alternarAreaMax`, F10), rodapé da tarefa (`montarRodape`, `marcarTarefa`), tempos legíveis (`tempo`, `tempoTexto`; no servidor, `app/tempo.py`) |
| `39` | painéis por menu (1.34): barra de ícones `#atividades`, `pnAbrir`, `pnFixar`, coluna clássica (`rodovia_paineis=0`) |
| `40` | tema claro/escuro/Windows (`aplicarTema`; o `<head>` aplica o tema antes de desenhar) |
| `41` | progresso de tarefas e downloads (`progMostrar`, `baixarArquivo`; links `/api/…` de arquivos passam por ele) |
| `42` | comandos contínuos (`cmdRep`, `pedirProximo`), ferramenta que continua após Enter, Esc no arraste |
| `43` | obras do PER: lista, importação (Excel/CSV/MS Project XML), ferramenta `obra`, faixas no editor (servidor: `app/obras.py`, `app/planilha.py`, `app/obras_video.py`, `app/rotas/obras.py`) |
| `44` | seleção precisa (`hitObjects`, `DPR`, alternância, realce) e propriedades que gravam ao sair do campo |
| `45` | menus Windows: ícones de linha (`ICO`, `icoPara`) e submenus ao lado |
| `46` | tela simplificada no modo painéis (ferramentas em grupos suspensos, sem repetições) |
| `47` | câmera por pontos-chave (`camera_keys`, `adicionarVista`), clima, sol e antes/depois (servidor: `app/ambiente.py`) |
| `48` | vegetação (ferramenta `veg`: árvore, pincel, área), caminhos de pedestres, frota e abrir DWG (servidor: `app/vida.py`, `app/dwg.py`) |
| `50` | Desktop Workspace: viewport dominante, painéis encaixados, linha de comando retrátil e modo Projeto. |
| `51` | Professional Shell: quatro hubs principais (Projeto, Layers, Propriedades, Vídeo) e faixa de opções deduplicada. |
| `99` | despachantes dos registros (ficam por fora de tudo) e a estrutura em Ajuda › Sobre |

### Como acrescentar uma função

**Ferramenta** (botão na barra, clique na tela, Enter, Esc, opções):

```js
ferramenta('minha',{rotulo:'✚ Minha ferramenta',dica:'O que fazer…',icone:'M4 4h16v16H4z',antesDe:'linkforce',
  clique(w,e){ /* w = ponto no mundo */ },
  concluir(d){ /* Enter com draft.type==='minha' */ },
  opcoes(el){ el.innerHTML='…' },
  esc(){ setTool('pan') },            // devolva false para seguir o Esc padrão
  entrar(anterior){}, sair(proxima){}});
```

**Comando da linha de comando**: `comando(['MEU','MC'],raw=>{…},'Ajuda que aparece na lista de comandos')`.

**Faixa de opções / menu Arquivo**: `itemFaixa('Aba','Grupo',['Rótulo','ícone',()=>…,1])` e `itemArquivo('depois de…',['Rótulo',()=>…])`.

**Mudar o que uma função existente faz** (desenhar algo a mais, um campo a mais no painel): `estender('draw', anterior => function(){ anterior(); … }, 'rótulo')`. A ordem fica registrada em `EXTENSOES` e aparece em Ajuda › Sobre › Estrutura da interface. Nunca use o padrão antigo `{const _x=f;f=function(){…}}`: o teste `test_v131` recusa.

Registros e nomes repetidos dão erro na hora (ferramenta ou comando com o mesmo nome; variável global repetida entre arquivos — teste).

## Estilos (`app/estilo.css`)

As cores principais estão em variáveis no `:root` (ex.: `--fundo`, `--painel`, `--texto`, `--azul`). Um tema claro completo pode ser feito trocando as variáveis num bloco `:root[data-tema="claro"]`.

## Rede de proteção (testes)

- `pytest tests` — todos os testes (API, vídeo, tela no Chromium).
- `tests/test_v131.py` — estrutura: módulos JS, nomes globais repetidos, extensões válidas, ESLint (quando disponível), nenhum nome indefinido no Python (`tests/nomes_indefinidos.py`), nenhuma rota da 1.30 perdida (`tests/rotas_api_1_30.json`), registros coerentes na tela.
- Regressão do vídeo TH57 (quadros 14, 40 e 96 s e vista do trevo) comparada pixel a pixel antes de cada entrega.


## Leitor ECW (`app/ecw_engine.py`, 1.38)
- `install()` só aceita rodas prontas (`--only-binary=:all:`). Ordem: pasta `pacotes_ecw` (sem internet) → pip com índice GWI + PyPI e o proxy do Windows → download direto (`_fetch`, urllib com proxy e certificados do Windows) da roda GDAL do GitHub de C. Gohlke (`GDAL_WHEEL_URL`, pela versão do Python) e da roda `gdal-ecw` do PyPI, guardadas em `pacotes_ecw` e instaladas sem internet.
- Falha: `_resumo()` resume a saída do pip (sem rastreamento), e a mensagem traz os 2 endereços e a pasta; o registro completo vai para `pacotes_ecw_log.txt`.

## Bordas sem dados da imagem local (`app/local_tiles.py`, 1.39)
- `nd_exact()`: pixel sem dados = todas as bandas no máximo do tipo (255/65535) ou 0. `collar_mask()`: na visão mais reduzida, componentes conectados (4-vizinhança) de `nd_exact` que tocam a beira, dilatados 2 px; guardada em `.<imagem>.borda_<tam>_<mtime>.npz`. `LocalMosaic.sample`, modo `borda`: transparente = `nd_exact` ∧ máscara da beira. Modo `auto` = regra anterior (≥253/≤3). Esquema 30 migra `auto`→`borda`.

## Rotas sem trechos curtos (`app/traffic.py`, 1.39)
- `origin_info`: comprimento de cada trecho original (antes de `split_contacts`) e se é fixo (eixo principal do DXF, manual, faixa de rota). `short_edges(min)`: arestas de origem < `min_route_segment_m` (exceto fixas, anel, rota). `make_itineraries(min)`: grafo local `conn` sem as curtas, com atalhos `connector(force=True)` entre quem chegava e quem saía delas (até 4 curtas em série; sem trocar de pista no canteiro), guardados em `route_connectors` (não entram em `connectors`, pintura nem editor). Entradas e saídas pela rede completa. Sem nenhum itinerário → refaz com 0.
