# Comparação de interface — uma execução por versão

Chromium em Linux, DXF sintético de 500 m, eixo de 400 m, imagem externa bloqueada. Nenhum projeto do usuário utilizado. Scripts executados com a mesma fixture geométrica, em processos separados, com carga de testes concorrente.

| Medida | 1.42.38 | 2.01 |
|---|---:|---:|
| Abrir interface | 1,898 s | 2,332 s |
| Abrir projeto e atualizar | 12,121 s | 8,967 s |
| Escala depois/antes de resize 1440×900 → 1024×650 | 0,682685 | 1,000000 |
| Deslocamento do centro mundial | 0 m | 0 m |
| Mediana do laço de desenho | 7,060 ms | 4,915 ms |
| RSS máximo Python | 442,5 MiB | 425,6 MiB |

Resultado determinístico de interesse: a escala deixa de mudar apenas porque a janela foi redimensionada. O centro já era conservado e continua conservado.

Os tempos são amostras únicas, não um benchmark estatístico. O laço de desenho não mede FPS interativo e as cenas após resize têm escalas diferentes na versão antiga. Não inferir ganho geral de desempenho, redução garantida de memória, desempenho em DXF grande ou capacidade de operação em Windows/8 GB. RSS não inclui o navegador nem a memória total do sistema.

Dados brutos em medicao-interface-antes.json e medicao-interface-depois.json. A conferência de invalidação dos caches é funcional: alterar aparência reconstrói a camada técnica sem incrementar backgroundBuilds no cenário controlado.
