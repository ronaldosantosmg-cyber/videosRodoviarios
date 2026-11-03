# Validação — Studio 3.14

## Inicialização

Foi reproduzida uma falha real da lógica anterior em cenário sintético controlado: dois itinerários na mesma pista, semente 1729, nove veículos semeados, folga de 6,901 m em t=0 e bloqueio da regra de ouro. Após a correção, o cenário admite cinco veículos e não registra violações.

A reprodução confirma a classe da falha descrita no texto recebido, não o ponto exato 1.671,72 m/percurso 4 citado nele. Esse trecho foi recebido como citação, sem um novo projeto correspondente.

Testes cobrem cinco sementes, vizinhança espacial incremental, links compartilhados através de conexão e faixas paralelas independentes. Um teste impede chamar a construção da ocupação global durante a semeadura.

## Diagnóstico e regressões

Rodada ampla: **126 testes aprovados**. Conferência dirigida adicional: **34 testes aprovados**, incluindo a entrada contínua a 5 km/h, com testes parcialmente sobrepostos à rodada ampla.

A mensagem de comboio retorna orientação de espaçamento e ação de correção dos fluxos, sem diagnósticos falsos de pedestres ou FFmpeg. Modo de tráfego incompatível, erros genuínos de pedestres e falhas de encoder conservam os tratamentos específicos.

A configuração e rede fornecidas anteriormente completaram os 220 s simulados sem violações após a nova semeadura, com 54 saídas. Isso não corresponde à codificação integral do MP4 de 6.600 quadros.

A validação dirigida não encerra as pendências históricas do repositório. O cache físico anterior é invalidado pela assinatura do código.
