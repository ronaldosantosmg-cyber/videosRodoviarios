# Rodovia Studio 1.22 — edição tipo CAD (inclui a 1.21)

Este pacote traz a **1.21** (pavimento rígido/flexível, representação escolhida, vídeo técnico ou artístico e contraste; veja ATUALIZACAO_1_21.md) e a **1.22** abaixo.

## O que mudou

### Seleção com grips (como no CAD)
- Com **Navegar / selecionar**, clique num objeto marcado. Vale para:
  - placa, intervenção, destaque, cidade;
  - faixa de pedestre, 3ª faixa, acostamento, seta de sentido;
  - acesso, fluxo incluído, zebrado, área de pista, faixas por trecho, interdição;
  - área sem sinalização, exclusão, travessia, sem conexão, OAE e alinhamento.
- O objeto selecionado mostra os **grips**:
  - arraste um grip para mudar o vértice;
  - arraste o objeto para movê-lo;
  - **Delete** apaga.
- Tudo entra no desfazer/refazer.

### Painel de Propriedades
- Mostra os campos do objeto: nome, textos, números, tipo, material, cor, ativo etc. Mostra também a **tabela de grips com X e Y em metros, com 3 casas (milímetro)**.
- Altere e pressione **Enter** para confirmar. Esc desfaz a digitação.
- Botões Mover, Apagar, Ver e Fechar.

### Linha de comando
- Fica abaixo da tela do editor. Com a tela em foco, o que você digita vai para ela.
- Comandos:

| Comando | Abreviação |
|---|---|
| MOVER | M |
| APAGAR | E, DEL |
| PROPRIEDADES | PR |
| ALINHAMENTO | AL |
| DIST | DI |
| ID, ZOOM, SALVAR, SNAP, ORTO | — |
| PLACA, AREA, ACOSTAMENTO, ACESSO, KMINI, KMFIM, PASSARELA, CHAMADA, DESTAQUE, OAE, FAIXA | abrem a ferramenta |

- Pontos podem ser digitados: `X,Y` (absoluto, no CRS do projeto) ou `@dx,dy` (relativo ao último ponto).
- **Enter vazio conclui o comando**. Esc cancela.

### Snap, orto e precisão
- **Snap (F3)** (desligado por padrão; a escolha fica lembrada) atrai o cursor para:
  - vértices e pontos médios do desenho (DXF/KMZ simplificado a 0,25 m);
  - grips das marcações;
  - eixo da via.
- O tipo de snap aparece ao lado do cursor.
- **Orto (F8)** trava o próximo ponto na horizontal ou vertical.
- O cursor mostra X/Y com 3 casas, e também a distância e o azimute desde o último ponto.

### Alinhamento por cliques
- Com **⟋ Alinhamento (cliques)** ou o comando AL, clique dois ou mais pontos sobre o eixo da via e pressione Enter.
- Depois de **Analisar arquivos**, ele passa a ser o **eixo de referência**: estaqueamento, câmera, sentido pelo eixo e revelação.
- A curva é suave e passa exatamente pelos pontos clicados. Nas Propriedades, `smooth` desligado deixa segmentos retos e `enabled` desligado volta ao eixo do DXF.
- O DXF não é alterado.

### Salvar, salvar como, excluir
- **Salvar projeto (Ctrl+S)**.
- **Salvar como…** cria uma cópia com outro nome. A cópia leva configuração, DXF/KMZ, imagens locais, camadas e elevação, sem caches nem vídeo.
- **Excluir projeto** move a pasta para `projetos\_lixeira`.

## Configuração
O esquema passou para a **versão 21** (campo do alinhamento do editor), com migração automática.

## Medido neste ambiente
- **Testes**: 206 testes automáticos passaram no pacote 1.22 (196 da 1.20 + 7 da 1.21 + 3 da 1.22). A 1.21 trouxe 7 testes novos e a 1.22, 3:
  - alinhamento: passa exatamente pelos pontos clicados, tem amostragem de ~1 m, é usado pela análise e pode ser desligado;
  - "salvar como" copia o projeto sem os caches;
  - editor no navegador:
    - seleção e propriedades;
    - coordenada do grip digitada (500201,237) e aplicada exatamente;
    - Enter e desfazer;
    - grip arrastado;
    - MOVER com `@1.5,-0.25`;
    - DIST de 3,500 m;
    - Delete;
    - snap a vértice do DXF;
    - AL por letras digitadas na tela;
    - Ctrl+S.
- **TH57 com a configuração padrão**: os quadros de 14, 40 e 96 s e a vista do trevo ficaram idênticos ao pacote 1.20, pixel a pixel. A medição foi feita com o código da 1.21; a 1.22 só acrescenta o editor e o alinhamento, que fica desligado sem pontos marcados.

## Não verificado / limitações
- Com a tela do editor em foco, letras e números vão para a linha de comando. Os atalhos F (tela cheia) e L (painel) funcionam quando o foco está fora da tela.
- O snap usa o desenho simplificado do editor (tolerância de 0,25 m). Para precisão total num vértice, digite a coordenada.
- Não há seleção múltipla (janela/crossing), copiar, girar nem escalar objetos.
