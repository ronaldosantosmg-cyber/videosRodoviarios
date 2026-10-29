# Testes dirigidos 2.01

Tentativa inicial: 28 testes aprovados, um caso falhou e apresentou erro de teardown devido à chamada de checkValidity no elemento dialog. Corrigido para validação dos campos individuais antes de desabilitar controles. Tentativa inicial preservada em dirigidos.xml.

Nova execução após a correção: 23 testes aprovados em 149,69 s, sem falhas. Incluiu seis regressões 2.01, interface contextual e regras de circulação da suíte existente. Evidências em dirigidos-confirmados.xml e dirigidos-confirmados/.

Casos novos: resize sem mudança de escala/centro, Aplicar e posterior descarte, falha de gravação sem perda de rascunho, validação antes do callback, lista CAD alfabética sem mutação da fonte, material no canvas sem POST de cálculo e sem reconstrução do fundo.

Medição isolada, uma execução por versão, DXF sintético de 500 m, eixo de 400 m, pavimento de 40 m, cena 1280 px/3 s, Linux:

| Medida | 1.42.38 | 2.01 |
|---|---:|---:|
| Preparação Scene | 1,117 s | 1,326 s |
| Preparação 3D | 1,623 s | 1,395 s |
| RSS máximo do processo | 300,3 MiB | 298,6 MiB |
| Itinerários | 1 | 1 |
| Veículos amostrados no 3D | 1 | 1 |

Amostra única, com carga de testes concorrente: não demonstra ganho global. O foco mensurável da revisão é evitar mudança de zoom e reconstrução do fundo por aparência. Abertura de DXF grande/PC Windows 8 GB não foi medida neste ensaio. Arquivos medicao-antes.json e medicao-depois.json preservam os valores.
