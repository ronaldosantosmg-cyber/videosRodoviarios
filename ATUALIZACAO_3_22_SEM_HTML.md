# Complemento Rodovia Studio 3.22 sem HTML

Arquivo: `RodoviaStudio_3_22_sem_html.zip`.

Por solicitação do proprietário, este pacote omite todos os arquivos `.html` e `.htm`. Ele contém 662 arquivos de produção; os demais arquivos são idênticos aos do pacote completo 3.22. O manifesto tem integridade recalculada e exige base mínima 3.18.

## Uso

Aplicável somente a uma instalação funcional 3.18 ou posterior, com `app/index.html` e `app/ajuda.html` já presentes. Não serve para instalar do zero ou restaurar HTML que o antivírus tenha removido.

O atualizador aplica o complemento sem substituir nem apagar os HTML existentes. Use o mecanismo de atualização já instalado, com o aplicativo fechado e depois da verificação pelo antivírus/TI.

A retirada do bloqueio por comboio e a correção de juntas da 3.22 estão incluídas. Como os HTML antigos são preservados, os textos incorporados nesses arquivos, inclusive rótulos e partes da ajuda, podem continuar descrevendo o comportamento de uma versão anterior. A decisão de exportação atual está em `fleet_policy.py`: comboio permanece no diagnóstico sem bloquear; colisões físicas continuam bloqueando.

## Testes

Script: `scripts/verificar_pacote_sem_html.py`.

- Zero HTML/HTM no ZIP; comparação byte a byte dos demais arquivos com o pacote completo 3.22.
- Aplicação sobre instalações completas 3.18 e 3.21, geradas em pastas temporárias.
- SHA-256 de `index.html` e `ajuda.html` preservado após aplicar e reverter.
- Servidor e interface abrem; sete menus carregam, projeto abre e modo Noite é salvo no Chromium.
- Política carregada do programa instalado não bloqueia o diagnóstico de comboio informado; continua rejeitando colisão física.
- Reversão retorna à versão base e instalação do zero é recusada pelo atualizador.

Relatório: [sem_html.json](validacao/3.22/sem_html.json).

## Antivírus

A ausência de HTML não comprova a causa ou a resolução de `Trojan:Script/Ulthar.A!ml`. O motor Microsoft Defender não está disponível neste ambiente Linux; não foi possível homologar o ZIP no Defender. Se houver alerta, manter em quarentena e encaminhar à TI/Microsoft. Nenhuma proteção, exclusão ou política de execução foi alterada. Nenhum arquivo HTML foi renomeado ou disfarçado em outro formato.
