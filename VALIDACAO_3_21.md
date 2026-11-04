# Validação da distribuição 3.21

Escopo: organização do pacote de produção e revisão dos caminhos de inicialização/atualização. Não há alteração da lógica do motor de tráfego da 3.20.

## Inspeção

- Revisados inicializadores CMD/PowerShell, preparação Python, atualizador temporário e atualizador de produção. Nenhuma alteração para desativar o Defender, adicionar exclusões ou contornar a política de execução foi introduzida.
- O inicializador chama Python local; a preparação usa ambiente virtual e pip isolado, binários e hashes no lock Windows. A instalação de dependências permanece sujeita à aprovação da TI e à cadeia de fornecimento dos pacotes; o ZIP não contém essas dependências baixadas posteriormente.
- O atualizador chama processos com argumentos explícitos e confere conteúdo/hash do pacote. Não foi substituído por um downloader remoto.
- Confirmada a ausência de dependência do aplicativo em testes/fixtures e executores de desenvolvimento removidos da distribuição. O código de testes permanece no repositório.
- A correspondência dos arquivos do ZIP com os arquivos do repositório, o manifesto SHA-256, caminhos internos e integridade do arquivo compactado é conferida durante o empacotamento/validação.

## Verificações executadas

`test_v14225_protection.py`: 17 aprovações, cobrindo gravação atômica, recuperação de configuração, proteção contra links, rejeição de origem web indevida e preservação da política de execução nos scripts. Esses testes não são análise antimalware.

## Limites

Uma inspeção de código e verificação de hashes **não** substituem o Microsoft Defender. Este ambiente não dispõe do motor nem das assinaturas do Defender para reproduzir `Trojan:Script/Ulthar.A!ml`. Não foi realizada submissão à Microsoft, análise de todos os fornecedores de dependências, assinatura Authenticode ou certificação de ausência de malware.

Não é possível declarar a detecção resolvida antes da verificação no Windows. Em caso de alerta, preservar a quarentena e submeter à TI/Microsoft; não instalar por exclusão de antivírus. A redução do conteúdo do pacote não é evidência de falso positivo.

As regressões físicas e de interface das versões 3.19/3.20 são descritas em seus relatórios; não foram todas repetidas, pois o motor e a interface funcional foram preservados.
