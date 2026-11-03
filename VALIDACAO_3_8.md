# Validação dirigida — Studio 3.8

Executada em 03/11/2026, Linux/Python 3.12, Node e Chromium. O aplicativo existente foi atualizado.

- **141 testes passaram**, com dois testes históricos de relatório/API desmarcados na seleção dirigida. Regressões incluem tráfego, filas, cancelamento, reservas, MP4 dia/noite, materiais e zebrados.
- DXF real gerado em teste: taludes genéricos verde BYLAYER e vermelho true color, vazios, precedência da cor da entidade, cadastro explícito preservado e classificação ambígua reportada.
- Materiais chegam ao render e à cena 3D nas novas cores; taludes não recebem automaticamente solo/pedra do catálogo. MP4 HD de 3 s, 24 FPS e 72 quadros foi decodificado integralmente, além dos testes de exportação existentes.
- Chromium: textura de grama para ambos os tipos em 2D/3D, médias de cores, cor manual e vazios preservados.
- Zebrados: segmento longo com ponto médio fora, anel interno sem corda, furo preservado, DXF explícito intacto, PARE/faixas mantidos e gores automáticos recortados antes de hachurar. As rotas permanecem inalteradas nos testes de integração.
- Testes de navegador: nove painéis em quatro resoluções sem deslocar o canvas, aplicar/cancelar/fechar, ajuda com versão e comandos atuais, dia/noite, pipeline de imagens e pooling 3D.
- O teste de descarte de imagens passou a controlar a liberação da decodificação por uma barreira explícita, evitando depender de uma espera de 30 ms em ambiente compartilhado.
- Pacote conferido por manifesto/hashes, sintaxe, aplicação sintética, importação, reversão, componentes e servidor real. O portão usa `--sem-suite`: a suíte histórica completa não é executada nessa etapa.

## Imagem de conferência

[Prévia de taludes em 1280×720](proveniencia/visuais-3.8/taludes-dxf.png). Desenho sintético para teste; títulos, km e geometria da imagem não representam o empreendimento do usuário.

## Desempenho

[Dados brutos](proveniencia/medicoes-3.8.json): nove repetições do sombreamento HD de taludes mistos. Mediana 40,364 → 37,055 ms, cerca de 8,2% de redução, com os mesmos pixels. A grama passa de duas para uma amostragem nessa etapa. Não é uma medição do tempo total de renderização nem do projeto do usuário.

A classificação evita construir índices de proximidade quando os tipos já estão resolvidos. O recorte da sinalização usa índice espacial para limitar candidatos. Resolução, FPS e parâmetros de qualidade do encoder continuam os configurados.

## Limites

O DXF específico da rotatória não estava disponível: a confirmação artística e geométrica naquele arquivo continua necessária. Contornos inválidos/virtuais não são usados para remover linhas; orientação ambígua exige conferência. A cor é evidência apenas para entidades já reconhecidas como taludes, com precedência do cadastro explícito.

A suíte histórica completa e as pendências registradas em `PENDENCIAS_3_6.md` não foram encerradas por esta entrega. Não foram medidos GPU física, Windows/WebView2 nem o empreendimento que levou 40 minutos. As automações Linux/Windows do GitHub verificam a publicação adicionalmente.
