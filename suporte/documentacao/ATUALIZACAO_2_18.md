# Atualização 2.18 (não validada pelo gate completo)

## Ícones
- Todo ícone automático é SVG de traço (cor do texto); fallback de emoji removido.
- Glifos novos: congelar, descongelar, mais, robô, comparar, alvo, aviso.
- Dedupe: ícone próprio vence o automático; nunca dois no mesmo comando.
- Botão só de ícone ganha title/aria-label.
- CSS: coluna fixa de 16 px (item sem ícone mantém a coluna), traço 1,7, modo de alto contraste.
- Teste: tests/test_v14247_icones_padrao.py.

## Linhas fantasma
- Retas de fechamento de hachura (inexistentes no DXF) ficam marcadas como 'virtual' e não viram linha no mapa nem linha de bordo. Com o DXF TH53 nenhuma ocorrência foi encontrada.
