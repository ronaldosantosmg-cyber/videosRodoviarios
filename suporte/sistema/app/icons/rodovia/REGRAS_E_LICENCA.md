# Rodovia Studio — Diretrizes Técnicas de Iconografia & Design System

## 1. Visão Geral
O sistema de ícones do **Rodovia Studio** foi concebido sob a perspectiva de um software CAD de engenharia de transporte, alinhamento horizontal/vertical e microssimulação de tráfego.

### Especificações Geométricas:
- **Canvas Base:** 24 × 24 px (viewBox="0 0 24 24").
- **Área Útil / Live Area:** 20 × 20 px com margem segura de 2 px.
- **Espessura de Traço (Stroke):** 1.85 px nominal (ajustável de 1.75 px a 2.0 px por CSS).
- **Terminações:** `stroke-linecap: round; stroke-linejoin: round;` com cantos discretamente suavizados.
- **Coloração Dinâmica:** `currentColor` como padrão, permitindo herança direta de cor de texto, botões e temas. Cores pontuais semânticas foram aplicadas unicamente onde a norma técnica exige (ex: zebrado amarelo `#FFCC00`, pendência `#F59E0B`).

---

## 2. Solução das Distinções Críticas do Domínio

| Par de Conceitos | Distinção Visual Implementada |
| :--- | :--- |
| **Salvar × Atualizar Cálculos × Redesenhar** | *Salvar* usa o disquete clássico de gravação de arquivos; *Atualizar cálculos* utiliza ciclo de setas com núcleo de processamento; *Redesenhar* utiliza setas circulares sobre a viewport para regenerar a tela gráfica (regen). |
| **Apagar Objeto × Desativar Circulação × Cancelar Tarefa** | *Apagar* usa a lixeira CAD tradicional; *Desativar circulação* preserva a infraestrutura ferroviária/rodoviária com indicador de interdição; *Cancelar tarefa* usa um círculo delimitador com "X" de abortamento imediato de thread. |
| **Recortar Segmento × Recortar Imagem** | *Recortar segmento* adota tesoura de precisão seccionando vetor linear; *Recortar imagem* emprega alças ortogonais clássicas de crop de fotografia/ortofoto. |
| **Unir Segmentos × Conectar Vias por Nó** | *Unir segmentos* mostra duas polilinhas e setas de fusão direta de vértices contíguos; *Conectar vias por nó* evidencia o elemento topológico de nó circular onde múltiplos ramais se encontram. |
| **Inverter Sentido da Via × Inverter Estaqueamento** | *Inverter sentido* mostra vetores de fluxo opostos em faixas paralelas; *Inverter estaqueamento* opera sobre a progressão numérica das estacas (+20m). |
| **Seta de Diagnóstico × Seta de Pavimento** | A *seta de diagnóstico* é analítica e flutuante no grafo; a *seta de sinalização física* possui o mastro e a geometria regulamentada de pintura sobre o pavimento (RFF). |
| **Camada do Desenho × Material de Apresentação** | *Camadas* representam pilhas de pranchas geométricas transparentes; *Materiais* exibem a esfera/rolo com textura física PBR. |
| **Prévia × Simulação × Exportação de Vídeo** | *Prévia* possui moldura de monitor com play rápido; *Simulação* exibe nós com play dinâmico de tráfego; *Exportação de vídeo* exibe claquete/câmera com codificação. |
| **IA Sugerindo Correção × Aplicar Correção Validada** | *Sugerir correção* usa a lâmpada de insight neural emitindo proposta; *Aplicar correção validada* usa o escudo/check de aprovação definitiva do engenheiro. |

---

## 3. Autoria, Origem e Licença
- **Sistema:** Rodovia Studio Professional Road CAD Suite.
- **Autoria:** Design de Interfaces & Iconografia Técnica de Engenharia Rodoviária.
- **Origem:** Produção 100% vetorial proprietária em SVG puro, sem dependências de fontes externas ou CDNs.
- **Licença:** MIT License / Propriedade Comercial Rodovia Studio — Livre para incorporação nativa em instaladores Windows e interfaces Web locais.
