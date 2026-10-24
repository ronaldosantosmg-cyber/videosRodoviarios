# Rodovia Studio 1.42.1 — relatório desta revisão

**113 testes passaram; nenhum falhou ou foi ignorado.** Destes, 38 são testes no Chromium, incluindo um fluxo integrado com servidor e motor reais. A aplicação foi validada em Linux/Python 3.12; não foi executada nativamente no Windows.

## Conferências

- Pacote original 1.42: SHA-256 conferido com o valor informado pelo usuário.
- Atualizador: API com candidatos atuais, ZIPs atuais e legados, rejeição de caminhos inválidos e de hashes divergentes, arquivos inválidos em rejeitadas, lock de atualização e versões equivalentes.
- Snapshot completo antes da escrita, falha durante substituição e recuperação automática, falha de rollback e recuperação do estado anterior à tentativa, restauração após instalação movida e recuperação de transação interrompida.
- Projetos, KMZ, base persistente de GeoTIFF e vídeos preservados.
- Modelos numéricos, rotas menores que 50 m e tráfego robusto; geração de MP4 com leitura dos quadros, dimensões, fps e quantidade de quadros pelo OpenCV.
- Propriedades abre/recolhe e preserva o contexto ao redimensionar; menus em cascata e teclado; contexto conforme comando; comandos fora do canvas; resoluções 1024, 1440 e 1920 px.
- Motor/API/editor integrados: fluxo válido verde; alteração pendente amarela; desativação recalculada vermelha. Os quadros do renderizador permanecem idênticos antes/depois da coleta do diagnóstico técnico.
- Fontes Python compilados, sintaxe de todos os módulos JavaScript e dependências verificadas.
- C# compilado com e sem WEBVIEW2, usando DLLs Microsoft WebView2 1.0.2903.40. Splash executado em Mono/Xvfb: versão, fabricante e animação comprovados por dois quadros distintos. Para o teste Mono, a arte do ICO foi recodificada em BMP 32 px; o ICO do produto foi preservado.

## Teste do ZIP de entrega

O ZIP final foi aplicado sobre uma instalação temporária criada a partir do ZIP original 1.42. O servidor instalado foi iniciado por caminho absoluto, com outro diretório de trabalho, e respondeu com versão 1.42.1 e FFmpeg disponível. A API da sessão encerrou o processo com código zero. Depois de mover a instalação, o rollback recuperou todos os arquivos originais do programa byte a byte, removeu os novos e preservou os dados.

SHA-256 do ZIP final: `212dc86b6208cfd97b5cc066708f3762c550bd9956be060a9743e0912be4c891`.

## Evidências

- [Resultados e escopo](resultado.json)
- [JUnit](pytest-resultados.xml) e [log](validacao.log)
- [Conferência do pacote instalado](verificacao_pacote.json)
- [Modelar em cascata](142_03_modelar_cascata.png)
- [Motor e editor reais](142_11_motor_editor_real.png)
- [Fluxo desativado](142_12_motor_editor_fluxo_problema.png)
- [Splash — quadro A](splash_142_1_a.png) e [quadro B](splash_142_1_b.png)

## Instalação e limites

Salve e feche a 1.42 antes da primeira atualização. O pacote fica em atualizacoes/. Após aplicar, feche o aplicativo e execute sistema/COMPILAR INICIADOR.cmd para ativar o iniciador 1.4; apenas trocar Python/JavaScript não recompila um EXE já existente.

Execução do PowerShell, WebView2 e substituição de arquivos em uso no Windows continuam dependentes de conferência em Windows. Os testes usaram trecho sintético e fixtures, não um empreendimento completo. A revisão não certifica drivers ECW/GDAL nem desempenho de hardware do usuário. Os números históricos dos documentos importados não são resultados desta rodada.
