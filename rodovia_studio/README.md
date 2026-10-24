# Rodovia Studio — continuidade da 1.42

Base recebida: `atualizacoes/RodoviaStudio_1_42_atualizacao.zip`.
SHA-256: `33fec6d47baf56c56d9ab6b6f5b6c3b9a553c075f0af0727986ade3ceeb12db6`.

Os fontes editáveis ficam em `pacote/suporte/sistema`; o formato do pacote continua compatível com a instalação existente. O código `src/videos_rodoviarios` na raiz do repositório é um aplicativo anterior, separado deste Studio.

A revisão é **1.42.1**, para que uma instalação 1.42 reconheça a atualização. A branch de desenvolvimento é separada da `main`. O ZIP original fica preservado.

## Desenvolvimento e validação

Crie um ambiente virtual Python >=3.11 e instale `pacote/suporte/sistema/requirements-dev.txt`. Para o navegador, disponibilize Chromium (variável `CHROMIUM`, se necessário). Para validar o splash no Linux, disponibilize Mono, Xvfb e as DLLs WebView2 1.0.2903.40. O executável Windows não é executado como aplicativo Windows no Linux.

`python validar_entrega.py` executa as verificações e grava as evidências. `python validar_entrega.py --gerar` executa novamente a validação e gera o ZIP **somente após todas as verificações passarem**, sem testes ignorados. São necessárias as variáveis `MONO_ROOT` (raiz extraída dos pacotes Mono, opcional se instalado), `WEBVIEW2_LIB` (DLLs net462) e `DISPLAY` com Xvfb ativo. As dependências e bibliotecas conservam verificação TLS e de assinatura dos distribuidores.

Os ZIPs de entrega são gravados exclusivamente em `../atualizacoes/`. O pacote contém hashes por arquivo e relatório desta revisão. Não reutilize relatórios históricos como evidência da revisão atual.

## Instalação e limites

Salve o trabalho e feche a versão 1.42 antes da primeira transição para 1.42.1: o iniciador antigo ainda tem seu próprio comportamento de encerramento. Coloque o novo ZIP em `atualizacoes/` da instalação e use o comando de atualização existente. Para ativar as mudanças do iniciador, feche o aplicativo e execute `sistema/COMPILAR INICIADOR.cmd` após aplicar o pacote. O compilador já acompanha o .NET Framework; as DLLs WebView2 são obtidas pelo comando existente, com opção de pacote local.

Após recompilar, o novo iniciador salva a janela incorporada e solicita o encerramento controlado do servidor antes de aplicar futuras atualizações; operações em andamento adiam a atualização. A janela incorporada WebView2 é necessária para confirmar o salvamento automático. Sem ela, o iniciador adia a atualização automática em vez de encerrar uma página sem confirmar o salvamento; o fluxo pelo comando principal e pela tela do aplicativo continua disponível.

Os testes executados nesta máquina cobrem servidor/API, geração e decodificação de MP4, preservação dos dados, falhas do atualizador, Chromium e splash em Mono/Xvfb, além da compilação do código C# com WebView2. A execução do PowerShell, do WebView2 e a troca de arquivos em uso em Windows precisam de conferência em uma máquina Windows. Não há certificação de desempenho em projetos reais nem de drivers ECW/GDAL do usuário.
