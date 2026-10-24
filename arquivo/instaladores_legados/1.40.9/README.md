# Instalador legado 1.40.9 — arquivado

Arquivo enviado pelo usuário e preservado sem alterações. SHA-256: `883fc588d20ba94f8242dfc918d518b95871cf0fdfdf17a347e67c515e6ad4e6`.

`INSTALAR_ATUALIZACAO.cmd` apenas muda para sua própria pasta e chama `apoio/instalar.ps1` pelo PowerShell. Não calcula geometria, não gera tráfego e não renderiza vídeos. O auxiliar chamado não acompanha o arquivo enviado e não existe no pacote atual 1.42.2.

O lançador pertence à distribuição 1.40.9 indicada no próprio texto. Não é utilizado pelo fluxo atual e fica fora de `rodovia_studio/pacote`, sem execução automática. Não execute a cópia arquivada para instalar a revisão atual.

A revisão atual recebe ZIPs na pasta `atualizacoes/` da instalação; o aplicativo/iniciador e `sistema/programa/atualizar.ps1` acionam `atualizador.py`, que valida, faz snapshot e aplica ou restaura os arquivos. O comando de recuperação `sistema/ATUALIZAR RODOVIA STUDIO.cmd` foi mantido: ele localiza a instalação e chama o atualizador atual. Arquivar este lançador externo não remove o atualizador.

## Gravação no PC

O Rodovia Studio executado no Windows grava seus projetos em `<instalação>/projetos` e os vídeos em `<instalação>/videos`. Essas pastas precisam permitir gravação pela conta do Windows que executa o aplicativo. Uma instalação numa pasta do próprio usuário evita depender de permissão administrativa. As permissões podem ser conferidas no Explorador, em Propriedades > Segurança.

Para receber uma atualização, baixe o ZIP do GitHub e escolha `atualizacoes/` da sua instalação como destino no diálogo Salvar como. O aplicativo local acessa essa pasta. O agente executado no ambiente de nuvem não acessa o disco do PC apenas por receber seu caminho; não existe vínculo automático entre os dois sistemas de arquivos.

O arquivamento foi feito no repositório; não moveu nem apagou arquivos do PC do usuário e não alterou os ZIPs 1.42.2 já validados.
