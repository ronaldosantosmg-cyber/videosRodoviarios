# Rodovia Studio 3.21 — pacote de produção

Esta distribuição consolida as correções de tráfego, menus, iluminação, materiais e manutenção já presentes na 3.20. O motor de tráfego não foi modificado; não há nova fase de aquecimento ou codificação.

## Conteúdo de instalação

O pacote padrão deixa de distribuir a pasta de testes de desenvolvimento, fixtures, a cópia histórica do atualizador usada pelos testes, requisitos de desenvolvimento, executores de testes visuais e o portão de qualidade. Esses recursos permanecem no repositório para desenvolvimento. Os arquivos usados pelo aplicativo, recursos visuais, inicializadores e atualizador de produção são mantidos.

A documentação de abertura foi alinhada com o inicializador existente: Python 3.12 x64. Quem já possui a instalação funcional não precisa reinstalar Python para aplicar esta atualização.

Não se remove automaticamente conteúdo de desenvolvimento que já exista em uma instalação anterior. Não se alteram configurações do Defender, políticas corporativas, exclusões ou estado de quarentena.

## Detecção do Microsoft Defender

O ZIP 3.20 foi sinalizado como `Trojan:Script/Ulthar.A!ml`. O usuário informou que os quatro arquivos da interface e o `simulation.py` baixados individualmente não foram sinalizados. Isso não identifica qual conteúdo disparou o alerta nem comprova ausência de ameaça.

**A retirada de conteúdo de desenvolvimento é organização do pacote de produção; não é uma correção comprovada da detecção. Este ZIP ainda precisa ser examinado pelo Defender no Windows.** Não houve análise com o motor do Defender neste ambiente Linux, nem envio/submissão de amostra à Microsoft. A detecção não é declarada falso positivo ou resolvida.

Para homologação: manter o antivírus atualizado, verificar o ZIP e a pasta de destino com o produto corporativo e consultar o Histórico de proteção. Se houver detecção, manter em quarentena e encaminhar à TI e à [análise oficial da Microsoft](https://www.microsoft.com/en-us/wdsi/filesubmission), com o hash do ZIP, nome da detecção e versão das assinaturas. Não restaurar/excluir da verificação apenas para instalar.

O ZIP acompanha manifesto por arquivo e SHA-256 externo. Hashes conferem integridade e correspondência com a versão publicada, mas não são laudo antimalware nem assinatura digital.

Consulte [a validação](VALIDACAO_3_21.md). Para uso após a aprovação do antivírus/TI, aplique pelo atualizador existente: projetos e vídeos não fazem parte do pacote.
