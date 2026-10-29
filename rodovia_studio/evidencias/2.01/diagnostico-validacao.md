# Diagnóstico da primeira regressão completa

Executada sobre o produto 2.01: 977 casos, 971 aprovados e seis falhas, sem ignorados. Duração de 2471,50 s. O empacotador bloqueou corretamente o ZIP.

- Duas falhas comparavam literalmente a orientação antiga “Linhas de bordo não são barreiras”. As verificações de geometria, motivo e ponto crítico passaram. Atualizadas para a nova orientação “Contornos decorativos e bordos não são barreiras”, mantendo as verificações de impedimento físico.
- Reconexão: a resposta terminal simulada podia chegar pela consulta automática antes de Playwright clicar em Retomar, ocultando o botão. O teste agora libera a resposta pelo clique real, sem forçar cliques ou chamar o handler diretamente.
- Link de semáforos: o teste calculava as coordenadas do clique imediatamente após expandir o ribbon, antes do resize agendado. O helper local aguarda dois frames antes de calcular a coordenada e clicar. O mesmo caso passou isoladamente antes desse ajuste.
- API/diagnóstico: duas tarefas foram marcadas como interrompidas. Consultado o banco de teste: render recebeu “Aplicação reiniciada. Inicie a tarefa novamente.”; análise recebeu “Processo sem resposta ou interrompido. Consulte o log e gere novamente.” O gate usa uma raiz de dados compartilhada pelos processos de teste. A repetição é serial para evitar concorrência entre essas instâncias de teste. Isso não comprova por si só a causa de interrupções no PC do usuário.

Nenhuma dessas adequações alterou o código de produto após a primeira regressão. A retomada verifica o hash do produto e repete módulos alterados, dependentes e falhos. Também foi reforçado o teste de aparência para observar os endpoints reais de cálculo e o de falha de Aplicar para executar uma nova tentativa de gravação efetiva.

Limitação da infraestrutura: não presumir que novos testes concorrentes de servidor possam compartilhar o mesmo banco. Isolar dados por worker em uma futura revisão do harness exigirá validar novamente todos os casos afetados; nesta entrega os módulos envolvidos serão repetidos em série.
