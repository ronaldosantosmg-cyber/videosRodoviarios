# Correção do acompanhamento e fila — após 1.42.37

O log informado mostra interrupção da consulta do andamento e rejeições na fila após dois minutos. A causa da primeira consulta perdida não pode ser determinada apenas pelo texto enviado.

## Correção no código

- Reconexão de leitura na mesma tarefa: espera progressiva de 1 a 15 segundos, consulta com limite de 15 segundos, sem reenviar o cálculo. Uma notificação por período de indisponibilidade; o contador de tentativas aparece no rodapé.
- Consultas simultâneas compartilham o acompanhamento. Retomar e o evento online antecipam a próxima consulta; não criam outro cálculo.
- Retomar estava após um controle dentro de uma seção oculta. Agora fica visível no rodapé compacto, com nome acessível completo e ajuda.
- Retirado o limite arbitrário de dois minutos da espera na fila. Limpar fila continua descartando pedidos pendentes, sem cancelar o cálculo atual.
- A fila aguarda também a aplicação do resultado recuperado antes de permitir outro processamento. Pedidos equivalentes continuam compartilhando a mesma operação.
- Avisos de vídeo e lista de resultados reutilizam a resposta final, eliminando duas consultas redundantes.
- Erros HTTP não transitórios mantêm o bloqueio e a orientação explícita; não autorizam um novo cálculo automaticamente. Falhas reais de processamento continuam sendo exibidas.

## Testes desta correção

18 casos aprovados, zero falhas/erros/ignorados. Interface real em Chromium; APIs controladas para falhas e um ensaio com servidor real, interceptando a conexão do GET de status. O ensaio do servidor confirmou exatamente um POST de cálculo, conclusão e resultado no editor. Não é reprodução do projeto exato nem homologação Windows.

Os testes cobrem também retomada manual, cancelamento, mudança de projeto, erro de permissão, permanência da vista e fila após cinco minutos de relógio simulado. XML e hashes em pytest.xml e resultado.json; capturas PNG e log nesta pasta. A primeira rodada de 17 casos está separada em primeira-rodada.xml. O novo módulo integra a lista obrigatória de validar_entrega.py para a próxima entrega.

## Estado da distribuição

Correção na branch desenvolvimento/rodovia-studio-1.42. Nenhuma alteração na main. O ZIP histórico 1.42.37 não foi modificado e ainda não contém esta correção. Não foi gerado novo ZIP nesta etapa; a suíte completa da próxima revisão continua necessária para empacotar. A nota de referência 7,8/10 não foi elevada por estes testes dirigidos.
