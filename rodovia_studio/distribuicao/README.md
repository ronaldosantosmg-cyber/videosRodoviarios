# Rodovia Studio 2.02 — instalação nova r2

Complemento da revisão 2.02. Não modifica o ZIP de atualização nem o código-base aprovado. Gera um assistente Windows x64 com fabricante **Ronaldo Santos**, Python local e preparação online das bibliotecas. Não é um pacote totalmente offline.

## Instalar

1. Baixar e extrair o ZIP inteiro, mantendo `payload/`, `distribuicao.json`, `instalar.py` e o executável juntos.
2. Executar **INSTALAR RODOVIA STUDIO.exe**, escolher uma pasta nova e clicar Instalar.
3. Aguardar as verificações. Ao concluir, Abrir pasta → **Rodovia Studio.exe**.

Windows 10/11 x64, .NET Framework 4.8, internet e pelo menos 3 GiB livres. Não precisa instalar Python previamente ou solicitar elevação pelo instalador. O ZIP tem 26.924.588 bytes; as 36 bibliotecas/FFmpeg somam 196.588.159 bytes de download. Os wheels são mantidos localmente para a preparação futura.

O instalador nunca sobrescreve uma pasta existente. Antes da criação do destino, falha/cancelamento remove somente seu temporário. Se a verificação no caminho final falhar, a pasta permanece marcada como incompleta para diagnóstico; eventuais arquivos recebidos nela são preservados. Logs: `%LOCALAPPDATA%\Ronaldo Santos\Logs`.

A instalação começa sem projetos. Dados anteriores permanecem na instalação anterior; não são apagados ou migrados implicitamente. Snapshot/rollback continuam no atualizador do aplicativo para atualizações futuras. Uma instalação nova não inventa um snapshot de versão anterior.

## Recursos

Inclui o mesmo aplicativo 2.02 (DXF, imagens, cálculos, tráfego, materiais, WebGL e vídeo), Python 3.12.10 do pacote oficial NuGet, iniciador compilado x64 e SDK WebView2 correspondente com loader x64/licença/avisos. Os wheels Windows CPython 3.12 são fixados por versão, tamanho e SHA-256, baixados do PyPI. Dependências, marcadores Windows e requisitos de versão Python foram conferidos em seus metadados reais.

O Runtime Edge/WebView2 é um componente do Windows: se indisponível, mantém-se o caminho de navegador do iniciador existente. Não instala runtime Microsoft silenciosamente. Pesos IA 3B, drivers/conversores proprietários ECW/DWG, credenciais e mapas online são opcionais/condicionais e não acompanham este kit. Não há promessa de todos os formatos/serviços externos sem esses recursos.

## Assinatura

**Este pacote NÃO tem assinatura Authenticode.** O titular informou não possuir certificado. `AssemblyCompany`/`AssemblyProduct` e a interface indicam Ronaldo Santos; isso não estabelece confiança pública ou elimina alertas do SmartScreen/Defender/política corporativa.

`assinar.ps1` prepara a assinatura real no Windows por certificado do titular em `CurrentUser\My`, com chave local, EKU Code Signing, cadeia/revogação válidas e carimbo de tempo do emissor. Não recebe PFX/senha, não cria certificado caseiro, não importa confiança e não altera antivírus/ExecutionPolicy. O certificado precisa ser adquirido/habilitado antes.

A sequência do construtor é: compilar iniciador → assinar iniciador, se configurado → calcular manifesto → compilar instalador com hash do manifesto embutido → assinar instalador → ZIP/SHA-256. Assinar ou alterar payload depois quebra a cadeia de hashes. Executar a publicação assinada em diretório de build separado e preservar este ZIP histórico; disponibilizar um novo artefato identificado. Não assinar este ZIP posteriormente como se os hashes continuassem iguais. Mesmo assinatura válida não garante ausência de avisos.

## Validação executada

- Aplicativo-base: verificador `validar_entrega.py --retomar .../entrega-validada --evidencias base-instalador`, com os 995 resultados do produto inalterado preservados por hash, nenhuma falha/erro/ignorado; splash/C# reexecutados. Não são 995 testes novos do instalador.
- Instalador: **20 testes novos aprovados**, sem falhas/erros/ignorados, cobrindo pasta existente, caminho com acento, traversal/link no ZIP, manifesto/payload alterado, origem HTTPS permitida, hash/tamanho de wheel, cancelamento e falhas antes/depois da criação do destino.
- Instalador e iniciador WebView2 compilados como Windows x64. Metadados de ambos: Ronaldo Santos / 2.2.0.0. Captura visual inspecionada em Mono/Xvfb.
- ZIP real: hashes de todo o payload conferidos, manifesto ancorado no executável, Python extraído, 36 wheels reais preparados e 270 arquivos do programa comparados byte a byte em destino novo com espaço/acento. Subprocessos Windows foram substituídos nesse ensaio Linux; não foi uma instalação Windows nativa.
- Todos os 36 wheels foram baixados e verificados; fechamento de dependências foi avaliado com marcadores Windows/Python 3.12.10.

Evidências em `evidencias/`: `testes.json`, `pytest.xml`, `instalador.png`, `dependencias-verificadas.json`, `pacote-real.json`, `pacote.json`, `distribuicao.json`. Relatórios `testes-iniciais.xml`/`testes-dirigidos.xml` são tentativas anteriores de desenvolvimento, não aprovação.

**Prontidão de distribuição: 6/10, piloto.** Faltam homologação nativa Windows/WebView2/8 GB, política corporativa, instalação em PC sem dependências, experiência de atualização/atalhos/desinstalação e assinatura válida. O aplicativo-base mantém a avaliação provisória da 2.02; não equivale a certificação normativa ou garantia universal de instalação.

## Reproduzir o build

No ambiente de desenvolvimento, obter wheels CPython 3.12 Windows x64 para `requirements-windows.lock`, com `pip download --only-binary=:all: --require-hashes --platform win_amd64 --python-version 312 --implementation cp --abi cp312`, e disponibilizar o SDK WebView2 original. O construtor valida os hashes do ZIP-base, do Python e dos wheels reais antes de gerar.

Executar `validar_instalador.py`, conferir a imagem, depois `gerar_instalador.py --cache <cache com python.3.12.10.nupkg e wheels/>`. `MONO_ROOT`, `WEBVIEW2_LIB` e `DISPLAY` apontam para as ferramentas Linux. Para build no Windows, usar o compilador .NET e o SDK correspondente. Assinatura opcional: `--certificado <thumbprint> --timestamp <URL HTTPS do emissor>`, em ambiente do titular com certificado válido e política PowerShell aprovada pela TI. Não enviar chaves ao repositório.

O builder recusa sobrescrever um ZIP existente. Publicar somente na branch de desenvolvimento; main não foi alterada.

## Revisão r2 do instalador

Usar RodoviaStudio_2_02_instalacao_completa_r2.zip. Inclui manifesto Win32 asInvoker/Windows 10/DPI em ambos os executáveis. O build Mono usa recursos_pe.py para conservar VERSIONINFO e incorporar RT_MANIFEST explicitamente; o construtor recusa executável sem asInvoker. Um candidato sem manifesto foi recusado na conferência e não foi publicado como r2. O ZIP inicial sem sufixo permanece histórico. Para repassar fontes/projeto a outra IA, consulte ../CONTINUIDADE_OUTRA_IA.md.
