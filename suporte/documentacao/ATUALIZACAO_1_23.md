# Rodovia Studio 1.23 — executável para Windows, com o programa em arquivos separados

## Como funciona
O Rodovia Studio passa a ter duas partes:

| Parte | O que é | Como atualiza |
|---|---|---|
| **Rodovia Studio.exe** (pasta principal) | Iniciador pequeno e estável. Prepara o ambiente, aplica atualizações, inicia, mostra a janela e encerra. | Quase nunca. Só quando o próprio iniciador mudar; nesse caso, um aviso pede para recompilar. |
| **suporte\sistema** (app, comandos, telas, motor do vídeo, atualizador) | Todo o programa, em arquivos separados (.py, .js, .html) | Pelo ZIP de atualização, como hoje, aplicado automaticamente pelo .exe |

Assim, novos comandos e correções chegam só pelo ZIP. O .exe não precisa ser trocado.

## Criar o executável (uma vez)
1. Aplique esta atualização como de costume (ATUALIZAR RODOVIA STUDIO).
2. Na pasta principal, dê dois cliques em **COMPILAR INICIADOR.cmd**.
   - Ele usa o compilador C# que já vem no Windows (.NET Framework 4, `csc.exe`), **sem administrador e sem baixar nada**.
   - O arquivo **Rodovia Studio.exe** é gerado no seu computador, com o ícone do aplicativo.
3. O .exe abre e cria o atalho **Rodovia Studio** na Área de Trabalho, substituindo o atalho antigo.

O código do iniciador fica em `suporte\sistema\iniciador\RodoviaStudio.cs`, para conferência pela TI.

## Vantagens de executável
- **Dois cliques e pronto**: sem janela preta do PowerShell e do Prompt.
- **Primeira vez ou dependências novas**: o .exe roda a preparação (Python, bibliotecas, FFmpeg) e mostra o andamento.
- **Atualização automática**: ao abrir, se houver ZIP de atualização em `atualizacoes` (ou em Downloads), o .exe aplica antes de iniciar e avisa o que mudou. Se a atualização falhar, o aplicativo continua na versão instalada e mostra o motivo.
- **Janela própria**: o aplicativo abre numa janela do Edge (ou Chrome) em modo aplicativo, sem abas nem barra de endereço.
- **Ícone perto do relógio**, com o menu:
  - Abrir Rodovia Studio;
  - Abrir pasta de projetos;
  - Procurar e aplicar atualização (fecha, atualiza e reabre);
  - Reiniciar o aplicativo;
  - Ver registro (logs);
  - Encerrar (encerra também a geração de vídeo em andamento).
- **Uma instância só**: abrir o .exe de novo apenas mostra a janela.
- **Proteção**: se o servidor do aplicativo parar, o .exe pergunta se deve reiniciar.
- **Registros** em `suporte\logs`: `iniciador.log`, `servidor.log` e `atualizacao.log`.

`ABRIR RODOVIA STUDIO.cmd` e `ATUALIZAR RODOVIA STUDIO.cmd` continuam funcionando como alternativa.

## Também nesta versão
- **Editor (Propriedades)**: nome ou título vazio e campo numérico vazio são recusados no próprio painel, com mensagem. O valor anterior é mantido.
- **Erro ao salvar**: se o servidor recusar uma alteração, o aviso "A alteração NÃO foi salva" aparece na área de mensagens, e não só no texto pequeno.

## Medido neste ambiente
- **Testes**: 210 testes automáticos passaram (206 da 1.22 + 4 novos):
  - o código do iniciador usa só recursos de C# 5 e tem tudo o que precisa;
  - o COMPILAR INICIADOR.cmd está em ASCII, com quebras de linha do Windows e UTF-8 para o compilador;
  - o `iniciar.ps1 -PrepararApenas` para antes de abrir o aplicativo;
  - o `run.py` informa a porta ao .exe, não abre o navegador e, se já houver um aberto, reaproveita aquele;
  - no editor, campos obrigatórios vazios são recusados.

## Não verificado / limitações
- **O .exe não foi compilado nem executado aqui**: este ambiente não tem o compilador do Windows e não consegue baixar um. O código foi conferido por leitura e por testes estáticos (só recursos de C# 5). Se a compilação falhar, o COMPILAR INICIADOR.cmd mostra a mensagem do compilador; envie-a para correção. O aplicativo continua abrindo pelo ABRIR RODOVIA STUDIO.cmd.
- **Antivírus ou política da empresa** (AppLocker/SmartScreen) podem bloquear um .exe sem assinatura digital, mesmo gerado no próprio computador. Nesse caso, a TI pode liberar a pasta ou assinar o arquivo.
- **Janela do Edge em modo aplicativo**: usa o perfil padrão do navegador. Sem Edge ou Chrome, abre no navegador padrão.
- **Troca do .exe**: o .exe em uso não se troca sozinho. Quando o iniciador mudar, feche-o pelo ícone e execute COMPILAR INICIADOR.cmd de novo.
