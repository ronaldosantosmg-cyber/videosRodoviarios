# Rodovia Studio 1.42

## Atualização autocontida
- A única pasta monitorada para atualização é `atualizacoes/`.
- ZIP solto na raiz é movido para `atualizacoes/` na organização automática.
- O atualizador aceita pacote atual com `manifest.json` na raiz do ZIP e pacote legado `pacote/manifest.json`.
- Pacote antigo é arquivado em `atualizacoes/aplicadas`; pacote inválido vai para `atualizacoes/rejeitadas`.
- O instalador externo apenas posiciona o ZIP em `atualizacoes/`; não extrai `pacote/`, `raiz/` ou `suporte/` na pasta principal.

## Atualização durante o uso
- O iniciador verifica `atualizacoes/` a cada 5 s.
- Ao detectar pacote novo, encerra servidor e janela própria do Rodovia Studio, aplica a atualização em processo externo e preserva rollback.
- Após sucesso, informa a nova versão e pede para reabrir o aplicativo.
- Edge/Chrome inteiro não é finalizado para não fechar outras abas do usuário.

## Splash
- Mostra a versão instalada.
- Mostra `Fabricante: Ronaldo Santos`.
- O logotipo gira, pulsa e esmaece enquanto o aplicativo prepara dependências, atualiza e inicia o servidor.
