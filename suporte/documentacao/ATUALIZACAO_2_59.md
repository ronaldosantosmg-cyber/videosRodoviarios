# Atualização 2.59 (não validada pelo gate completo)
## Logo
- Causa: o `Rodovia Studio.exe` era compilado sem o parâmetro de ícone, então saía sem o logo (barra de tarefas, atalho, tela de abertura).
- `COMPILAR INICIADOR.cmd` agora usa `/win32icon` com `rodovia.ico` (seu logo, 7 tamanhos).
- O iniciador também carrega `rodovia.ico` direto da pasta do programa, mesmo com um .exe antigo.
- Na janela do aplicativo o logo (cabeçalho, ícone, favicon) já aparecia; conferido por captura de tela.
- AÇÃO NECESSÁRIA: rodar `COMPILAR INICIADOR.cmd` (requer .NET Framework do Windows, sem downloads) para gerar um novo `Rodovia Studio.exe`. Não pude compilar nem testar o .exe aqui.

## Limpeza
- A Verificação passa a exigir `rodovia.ico`, `app/georas_logo.png` e `app/icone.png` (logo ausente vira erro de "ausente").
- A limpeza (LIMPAR E VERIFICAR.cmd) segue manual, com o aplicativo fechado; não foi executada na sua pasta.
