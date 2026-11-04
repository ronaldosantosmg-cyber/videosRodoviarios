# Validação 3.23

## Revisões independentes

Dois agentes revisaram atualização/launcher e identidade de processo. Achados confirmados no código anterior: ZIP de mesma versão ignorado por metadado; porta aceita apenas por status ok; versão do log relida do disco apesar de código antigo em memória. A revisão não teve acesso ao computador Windows do proprietário para afirmar qual dessas condições ocorreu lá.

## Testes dirigidos

- 31 testes aprovados: identidade real, fonte/versão alterados após importação, fonte removido, comparação de sessão, limpeza/quarentena, decisão de exportação com comboio, checkpoints/cache e MP4.
- 16 testes aprovados: reparação em versão igual, arquivo ausente, pacote idêntico, recusa de downgrade, falha de hash final com rollback, cache de mesmo tamanho/mtime, inicialização/encerramento real, reaproveitamento da sessão correta e higiene histórica.

Total: **47 testes dirigidos aprovados**. A suíte histórica integral não foi executada. Dois testes antigos de migração tiveram falhas também reproduzidas pelo revisor com o fonte original; não são declarados corrigidos.

## O que é verificado

- Código antigo que rejeita comboio é detectado pela prova da função carregada, mesmo se o arquivo/JSON no disco tiver aparência atualizada.
- O hash do código carregado é distinto do SHA-256 do arquivo observado. Hash de bytecode não é comparado como identidade universal entre interpretadores ou instalações.
- Mesma versão com fonte ausente/antigo é reparada com backup. A marca de versão sozinha não permite arquivar a atualização como aplicada.
- `VALUE=1` em bytecode antigo e fonte `VALUE=2` com mesmo tamanho/mtime passam a carregar `VALUE=2` após aplicar; usa cache verificado por hash.
- Pastas de outra instalação não são reutilizadas pela abertura Python. Uma sessão antiga ou sem identidade exige encerramento controlado; não mata processos indiscriminadamente.
- Cinco itens de desenvolvimento conhecidos vão para quarentena; restauração, retenção mínima de 30 dias, links, próprio script em uso e proteção de dados/recursos são testados.
- Exportação real de MP4 mantém comboio como diagnóstico e rejeita colisão/incompletude.

## Limites de plataforma e integridade

Testes em Linux/Python 3.12 e Chromium. Fonte C# revisado, mas não havia csc/mcs/dotnet/mono no ambiente; não foi compilado nem executado no Windows. O iniciador CMD/Python foi testado; não se distribui EXE novo.

Verificação do pacote, sintaxe, instalação/reversão e variante sem HTML são registradas nos relatórios em `validacao/3.23/`. A conferência de arquivos cobre os destinos incluídos no manifesto; os HTML preservados pelo complemento não passam a ser certificados pelo novo pacote.

Microsoft Defender não disponível. Nenhum alerta é declarado falso positivo ou resolvido. Não foram desativadas proteções, adicionadas exclusões ou restaurados arquivos em quarentena do antivírus.

O nome do complemento passou a `RodoviaStudio_3_23_atualizacao_sem_html.zip`, reconhecido também pelo atualizador antigo. O nome anterior sem “atualizacao” podia ser ignorado na descoberta automática. A interface permite verificar/reparar a mesma versão; o atualizador compara os arquivos antes de decidir reaplicar.
