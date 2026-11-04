# Validação 3.20 — menus e iluminação

Script: `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium python scripts/verificar_janelas.py`.

Verificação em Chromium real, Linux, com servidor local e projeto temporário. Resoluções: 1920×1080, 1366×768, 1024×768 e 760×620.

- Sete menus principais dentro da tela e acessíveis ao ponteiro, antes e depois da abertura de cada um dos nove painéis.
- Abertura do menu Cenas e Vídeo e visibilidade de Dia e noite com os painéis presentes.
- Arrasto de painel até o topo, redução e ampliação da janela: barra de menus permanece livre; painel e rodapé ficam dentro dos limites.
- Comando de modelagem com conteúdo alto e rolagem conserva seus limites abaixo da barra de menus.
- Aplicar, salvar, cancelar e descartar; área do Canvas e transformação da vista preservadas.
- Navegar pelo menu com alteração pendente não fecha o painel; selecionar Dia e noite solicita confirmação. Continuar editando mantém o rascunho e não abre o comando solicitado.
- Modos Dia/Noite/Transição aplicados, consultados pela API e preservados ao reabrir o projeto. Cancelar escolha não confirmada mantém o modo salvo.
- Auditoria de pórticos 12/18 m, reabertura de resultados sem novo processamento e consistência da configuração permanecem no roteiro.

O teste anterior sem painéis não detectava a sobreposição da barra por uma janela alta. O novo teste reproduziu essa falha antes da correção e passou depois.

A validação é de interface e persistência; não é nova avaliação visual de um vídeo completo em cada iluminação. O motor da 3.19 não foi alterado. Não foi necessário repetir toda a suíte física. Windows/WebView2 e combinações de escala/tela fora da matriz acima não foram executados.
