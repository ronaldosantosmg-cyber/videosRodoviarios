# Rodovia Studio 2.01 — entrega aprovada

[Baixar ZIP 2.01](https://raw.githubusercontent.com/ronaldosantosmg-cyber/videosRodoviarios/a410dac131f64573b069d0de7c1b65f8698494b5/atualizacoes/RodoviaStudio_2_01_atualizacao.zip)

12.196.927 bytes. Download HTTPS integral conferido: HTTP 200 e hash igual ao arquivo local.

SHA-256: `17e2626bc3e9a77cb6b3d653f4733d8d5161d16703228ddb16d8d4e820421183`.

## Alterações em relação à 1.42.38

- Redimensionamento conserva centro e escala em pixels CSS. A captura de imagem preserva a vista quando há referência válida.
- Aplicar no painel principal salva e mantém a janela; o descarte posterior retorna à aplicação confirmada mais recente. Salvar e fechar continua disponível.
- Formulários de modelagem validam campos antes do callback e mantêm o rascunho em falha. Salvar e atualizar usa a fila comum, sem uma segunda espera arbitrária de dois minutos.
- Ícones principais distintos, contraste e foco de teclado ajustados. Camadas e materiais em ordem alfabética/natural, preservando a ordem técnica das seções e itinerários.
- Materiais naturais em superfícies vetoriais 2D pelo catálogo existente, respeitando mapeamento por camada. Ativar em Cena → Materiais e texturas → Usar materiais naturais. Trata-se de amostra local, não identidade ou resolução equivalente ao render final.
- Aparência invalida a camada técnica sem reconstruir a imagem aérea ou iniciar cálculo apenas para redesenhar.
- Orientação de saída da superfície explica seção operacional, afastamento e apresentação fora do pavimento, sem suspender barreiras reais.

O motor de tráfego existente foi preservado. Não foi incluído outro simulador, alterada a matemática do arrasto ou declarado um cadastro veicular integralmente homologado pelo DNIT. Seções, nós, sentidos, interdições, semáforos e regras de OAE continuam no mesmo caminho de configuração, cálculo e vídeo.

A limpeza removeu o mecanismo duplicado de espera dos formulários. Módulos com rotas, registros ou chamadas dinâmicas foram mantidos: não havia prova suficiente para apagá-los com segurança. Não houve limpeza destrutiva de dados do usuário.

## Validação executada nesta revisão

- Primeira execução completa: 977 casos, 971 aprovados e seis falhas; o pacote foi bloqueado.
- Adequações de testes: duas comparações de texto atualizado, sincronização de Retomar e do clique após resize, reforço da verificação dos endpoints reais de cálculo e da nova tentativa após falha de gravação.
- API/diagnóstico foram repetidos em série após tarefas interrompidas na execução concorrente com banco compartilhado.
- Resultado aprovado: **977 casos, zero falhas, erros e ignorados**. Retomada com hash do mesmo produto: 897 aprovações preservadas e 80 casos repetidos, todos aprovados. Não foram reutilizados testes da versão 1.42.38 como aprovação do produto 2.01.
- MP4 2D/3D e imagem local + mapa: geração e decodificação nos testes, incluindo veículos e ausência de mensagens de ensaio nos quadros.
- Iniciador C# compilado com e sem WebView2; splash 2.01, fabricante e animação conferidos em **Mono/Xvfb, Linux**. Compilação apresentou aviso CS0162 existente; não é homologação nativa Windows.
- ZIP final instalado em caminho isolado com espaços/acentos: versão 2.01 conferida; projetos, KMZ, cache GeoTIFF e vídeo de teste preservados por hash. Rollback para 1.42.38 restaurou todos os hashes anteriores do programa.

Registros: entrega-validada/resultado.json, pytest-resultados.xml, retomada.json, validacao.log e pacote-real.json. Tentativas anteriores e diagnóstico preservados para auditoria.

## Medições e limites

Na comparação de resize 1440×900 → 1024×650, a escala depois/antes era 0,682685 na 1.42.38 e passou a 1,000000 na 2.01. O centro permaneceu inalterado nas duas versões. Dados e tempos em medicoes-interface.md e validacao-dirigida.md.

Os tempos de abertura/desenho e RSS são amostras únicas em DXF sintético, com carga concorrente; não demonstram ganho geral, FPS interativo ou capacidade em Windows/8 GB. Não foi reproduzido o projeto salvo específico do usuário.

Pendentes: validação Windows/WebView2 e carga prolongada em 8 GB; medição em DXF grande; conferência do projeto real; revisão normativa completa do cadastro/arrasto; núcleo CAD exato completo; reconhecimento semântico autônomo de imagens e pesos de IA local 3B. A assistência local existente foi preservada, sem executar código externo.

**Prontidão provisória para uso intenso: 6,5/10**, avaliação de engenharia, não certificação. Há evidência de melhora de operação e regressão automatizada; a experiência no projeto real continua necessária antes de atribuir nota 9.

## Atualizar

Salve e mantenha uma cópia do projeto. Coloque o ZIP em atualizacoes/ da instalação e use o atualizador do próprio Rodovia Studio, permitindo o encerramento controlado. Não extraia sobre o programa aberto. Schema 31 preservado; rollback para 1.42.38 conferido em ambiente isolado.

ZIPs históricos preservados. Entrega publicada somente na branch desenvolvimento/rodovia-studio-1.42. A main permaneceu no commit `4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3`.
