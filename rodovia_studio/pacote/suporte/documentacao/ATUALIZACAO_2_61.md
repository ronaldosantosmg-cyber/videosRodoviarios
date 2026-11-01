# Atualização 2.61 (não validada pelo gate completo)

## Falha que impedia o vídeo (confirmada nos logs do projeto)
- `KeyError: 'terrain'` em `render.chrome`: a legenda do cabeçalho incluía o papel Terreno, que não tinha rótulo. O processo auxiliar caía, o programa refazia em um processo e falhava no mesmo ponto, após 17–22 min de renderização (14:51 e 19:10 de 31/10).
- Correção: rótulo "Terreno" e `labels.get(...)` com fallback; teste `test_v14293_legenda_terreno.py`.

## Outros erros dos logs
- `Can't get local object 'make_chain.<locals>.<lambda>'` (30/10): já corrigido em versão anterior (`_KmChain`); não ocorre mais na 2.60.
- `reading 'key'` (tela): guardas em `drawSelection` (item nulo e `hotGrip.o` ausente).
- `reading 'camera'`: `worldToImg` devolve `[0,0]` se a vista ainda não existe.
- WinError 32 ao apagar vídeo: já tratado por `store.replace` (25 tentativas).
- 409/404 em editor.json, vectors.json e area: respostas esperadas (dados desatualizados / clique fora de área), não falhas.
