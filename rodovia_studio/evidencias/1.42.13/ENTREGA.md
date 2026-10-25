# 1.42.13 — continuidade dos fluxos

Correção direcionada ao uso dos eixos cadastrados e à remoção de interrupções artificiais. Não inclui reorganização da tela, camadas gráficas, fumaça ou pedestres previstos para outra revisão.

## O que mudou

- Todos os eixos habilitados do DXF participam como fontes nativas, inclusive os secundários; duplicatas do esqueleto são evitadas sem apagar ligações parcialmente sobrepostas.
- Fragmentos compatíveis da mesma camada/nível/sentido podem ser unidos na derivação: encontro único, até 0,25 m, tangentes em até 10° e passagem contida no pavimento. Não altera o original. Edições vinculadas suspendem junções; vínculos anteriores de cortes e desativações continuam válidos.
- Pequenos subtrechos internos pertencem ao eixo longo e não são eliminados como minirrotas independentes. Contatos quase coincidentes não apagam 1–3 m do eixo. Não geram pontos independentes de nascimento de veículos.
- Os eixos secundários válidos podem ter origem/destino próprios. Excedentes externos podem ser aparados; obstáculos e lacunas internas não viram portais ou atalhos.
- Suavização de itinerário inteiramente nativo limitada a 0,50 m de desvio; permanecem validações de movimento, sentido e superfície.
- Diagnóstico em português com motivo, localização e orientação de correção. Linhas de bordo não são obstáculos. Canteiros, obstáculos, exclusões e cortes continuam sendo respeitados.

## Uso

Instalar o ZIP por `atualizacoes/`, atualizar pelo Rodovia Studio e usar **Calcular e atualizar fluxos**. Selecionar o fluxo para conferir motivo e ponto vermelho. Quando faltar pavimento, revisar a classificação/hachura ou reposicionar a faixa. Para escolha explícita, **Rota de veículos → Selecionar uma linha / Seleção contínua**; para partes defeituosas, **Recuperar fluxo principal** conserva os restos revalidados sem conectar as lacunas.

## Evidências e limites

**91 testes direcionados aprovados**, zero falhas, erros ou ignorados, em 67,07 s. Abrangem fragmentação, eixos secundários, minirrotas, cortes, recuperação, desativações anteriores, bordos versus obstáculos, portais, movimento, colisões, pare e siga e seleção/propriedades no Chromium. Capturas: `14213_01_eixo_continuo_encontro.png` e `14213_02_bloqueio_localizado.png`.

DXF fornecido anteriormente: SHA-256 `7936e09e195212a85a894dbc48f5ad337f0cbe4f3195225e6f8137297e3e4538`. Analisados 31 eixos; uma geometria sem extensão válida não virou fonte. Produzidos cinco itinerários, todos revalidados geometricamente; maior itinerário: 286,26 m. Arquivo original preservado. O teste não usa o projeto salvo atual do usuário e não comprova a solução de todos os seus bloqueios.

Sintaxe Python/JavaScript e integridade do pacote verificadas. Iniciador C# compilado com e sem WebView2; splash conferido em Mono/Xvfb. Validação direcionada no fluxo simplificado solicitado; **a suíte integral não foi repetida**. Não houve execução nativa Windows/OneDrive/WebView2, certificação normativa nem ensaio prolongado.

Prontidão para uso intenso: **7/10 provisória**, sem aprovação integral. Mudança publicada somente na branch de desenvolvimento, com `main` preservada e sem promoção automática do canal estável.

## Artefato

`atualizacoes/RodoviaStudio_1_42_13_atualizacao.zip`, 3.376.967 bytes.

SHA-256: `90dd135ad8f734583a9911b0a4aa3b3b2c34881d3a807cac6e9d45f498edfb20`.

Fonte validada: `7863fa1004da07f5e2edf989268546935195fc470f1bd920254d1357d8879af9`.

Instalação sobre a 1.42.12 em pasta com espaços e acentos, inicialização fora da raiz e encerramento controlado aprovados. Após mover a instalação, rollback restaurou os arquivos anteriores byte a byte e preservou sentinelas KMZ, GeoTIFF e vídeo; o novo módulo nativo foi incluído na verificação do programa instalado. Relatório: `verificacao_pacote.json`.
