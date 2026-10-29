# Rodovia Studio — aplicação 2.02

Repositório de continuidade da 1.42; implementação mantida em `pacote/suporte/sistema`, schema 31. A branch de trabalho é `desenvolvimento/rodovia-studio-1.42`; não alterar/mesclar main sem autorização explícita. O CLI `src/videos_rodoviarios` da raiz é um aplicativo separado.

A versão efetiva deve ser conferida em `pacote/manifest.json` e `pacote/suporte/sistema/VERSAO.json`. Notas históricas não aprovam funcionalidades ou testes de uma revisão nova. Leia [AGENTS.md](AGENTS.md) antes de alterar.

## Usar e instalar

- Instalação existente: ZIP de atualização 2.02 em `../atualizacoes/`, pelo atualizador do próprio aplicativo. Preservar projetos, vídeos, fontes e cache GeoTIFF. Snapshot/rollback continuam disponíveis.
- Instalação nova: `RodoviaStudio_2_02_instalacao_completa_r2.zip`, extrair tudo e executar **INSTALAR RODOVIA STUDIO.exe**. Pasta nova, Python local e preparação online de bibliotecas/FFmpeg; Windows x64, .NET 4.8 e internet na primeira instalação. [Instruções e limites](distribuicao/README.md).
- A distribuição identifica **Ronaldo Santos** nos metadados. Ainda não há certificado Authenticode; isso não elimina avisos do Windows/SmartScreen ou política corporativa. Não alterar proteções para instalar.

## Conferência e desenvolvimento

[Guia para outra IA e projeto de reprodução](CONTINUIDADE_OUTRA_IA.md). [Evidências e limites da aplicação 2.02](evidencias/2.02/LEIA_ME.md). [Método de reconstrução](evidencias/2.02/metodo-e-cenarios.md).

Usar Python 3.12 e `pacote/suporte/sistema/requirements-dev.txt`. Chromium para testes de navegador. Mono/Xvfb e SDK Microsoft.Web.WebView2 para splash/compilação Linux (`MONO_ROOT`, `WEBVIEW2_LIB`, `DISPLAY`). A distribuição usa também recursos .NET de compressão e Web.Extensions. Bibliotecas extraídas no desenvolvedor não são prova de execução no Windows.

`python validar_entrega.py` executa a validação da aplicação; `--gerar` só empacota após aprovação. `--retomar` permite conservar resultados exclusivamente do produto com o mesmo hash, repetindo casos afetados. Produto alterado exige nova regressão. Não reaproveitar resultados da 2.02 para outra alteração do motor. O complemento usa `distribuicao/validar_instalador.py`, `gerar_instalador.py` e `conferir_pacote.py`, conforme seu README.

ZIPs de entrega exclusivamente em `../atualizacoes/`, sem sobrescrever históricos. Publicar link HTTPS conferido e SHA-256. Windows/WebView2/8 GB e carga prolongada precisam de homologação específica antes de distribuição pública em escala.
