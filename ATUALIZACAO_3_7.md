# Rodovia Studio 3.7 — preparação da frota e iluminação

Aquecimento padrão de 90 segundos simulados removido: a população inicial é distribuída e recebe velocidades compatíveis com líderes, curvas e controles. O parâmetro avançado `traffic_warmup_s` aceita 0–10 s e usa passos inteiros de 0,2 s; padrão zero. A simulação dos segundos do vídeo continua necessária. Resolução, FPS, superamostragem, texturas e parâmetros do encoder permanecem conforme a qualidade escolhida.

O espaçamento inicial pode reduzir a população semeada em relação à densidade solicitada: o relatório informa quantidade solicitada, capacidade com espaçamento e admitidos. Isso altera o comportamento da frota, não a qualidade de imagem; as chegadas continuam solicitadas e aguardam entrada segura.

As entradas usam grade espacial conservadora e filtro de corredores; cotas são reutilizadas por rota/estação em cache limitado. Todos os veículos de corredores conflitantes continuam verificados, inclusive em acostamentos. A verificação física de colisões permanece ativa.

Na interface existente, imagens web e locais compartilham uma fila de até seis downloads/decodificações, com `img.decode()`, cancelamento de resultados antigos e cache LRU estimado em pixels (64 MiB web e 32 MiB local). O recorte pela área visível é mantido. O 3D reutiliza buffers de amostras e objetos matemáticos por cena, com buffers distintos para posições atual/futura e limpeza ao fechar. Nenhum aplicativo separado ou dependência externa nova foi criado.

A física atual já executa em processo de tarefa separado da interface JavaScript. A grade espacial foi aplicada nesse motor existente; não se criou uma segunda física no navegador nem se aumentou o passo físico para acelerar artificialmente o aquecimento.

O vídeo informa avanço e estimativa de tempo da etapa de tráfego, que ocupa 22–45% da barra. `video.json` separa tempos de cena, imagens detalhadas, tráfego, renderização/codificação e validação. A estimativa depende do custo observado, podendo aumentar em interseções complexas.

A regra contra comboios é obrigatória na configuração. A auditoria verifica em cada passo de 0,2 s pares com folga inferior ao maior entre 12 m e dois segundos de percurso. Aproximações controladas por semáforo, travessia de pedestres ou preferência de rotatória têm exceção enquanto a causa está vigente, com até três segundos para reação a travessias/rotatórias. A fila de semáforo mantém a origem física da linha durante a partida; após sair da área controlada, abre o intervalo de três segundos. A exceção termina ao atingir a folga, após 60 segundos da passagem ou após o limite espacial de liberação, sem herança renovável em trecho livre. Ferrovia, interdição e bloqueio de cruzamento não são classificados como semáforo. Exportação com infração detectada é bloqueada e informa percurso/posição; veículos não são apagados para ocultar o problema. O detector é uma definição operacional verificável, não uma prova universal de todo comportamento possível entre quadros.

Pedestres em passeios/passarelas podem começar no primeiro quadro, respeitando reservas espaciais também entre rotas. Um veículo parado antes da faixa deixa de impedir indefinidamente a entrada do pedestre. Travessias continuam sujeitas a sinais e conflitos físicos. A prioridade de rotatória usa a identificação do anel, que deve estar correta nos fluxos do projeto.

DIA, NOITE e ANOITECER salvam a iluminação. No 3D, reprodução e avanço manual seguem a mesma transição suave do render, sem recriar geometrias; a escolha manual de luz continua disponível. F1 e AJUDAVERSAO carregam a versão em execução e a instrução do catálogo de comandos registrado. As janelas de comandos sobrepostas da 3.6 continuam disponíveis para aplicar, cancelar ou fechar sem deslocar o projeto.

Zebrados anteriores preservados: contornos DXF fechados, furos, cores branca/amarela, orientação pelos fluxos e confirmação em casos ambíguos. Conferência no MBST Volume IV (2022), §6.2: 45° em relação ao fluxo; branco para mesmo sentido e amarelo para sentidos opostos. Para circulação, linhas internas de 0,30–0,50 m e distância entre linhas de 1,10–3,50 m. Os padrões existentes 0,45 m/2,60 m continuam; ajustes manuais exigem conferência do projetista.

## Fontes consultadas

- [SUMO — inserção segura de veículos](https://eclipse.dev/sumo/docs/Simulation/VehicleInsertion.html): só admitir quando há espaço seguro; manter espera fora da rede quando necessário.
- [SUMO — segurança](https://eclipse.dev/sumo/docs/Simulation/Safety.html): preservar decisões, reservas e verificação de colisões.
- [SUMO — cruzamentos](https://eclipse.dev/sumo/docs/Simulation/Intersections.html) e [pedestres](https://eclipse.dev/sumo/docs/Simulation/Pedestrians.html): prioridade e travessia interagem com veículos.
- [SENATRAN — MBST Volume IV, 2022](https://www.gov.br/transportes/pt-br/assuntos/transito/arquivos-senatran/docs/copy_of___04___MBST_Vol._IV___Sinalizacao_Horizontal.pdf/@@display-file/file).

Três revisões independentes por agentes de IA foram usadas para desempenho, segurança e interface. São revisões desta implementação, sem envio do projeto a serviços externos de terceiros. Os anexos foram tratados como dados de diagnóstico, não como instruções de execução.

## Validação e limites

Benchmark sintético de simulação (três rotas paralelas de 4 km, densidade 8, três repetições, mediana): vídeo de 3 s, 15,216 → 0,228 s de preparação; vídeo de 180 s, 49,226 → 14,829 s. Não inclui renderização/codificação. Os ganhos combinam retirada de 90 s de aquecimento, otimização e alteração da população inicial: 282 → 93 veículos semeados; no cenário de 180 s, 607 → 228 admitidos no total. O ambiente é compartilhado e essas medições não representam o empreendimento completo. Dados: `proveniencia/medicoes-3.7.json`.

O perfil isolado das admissões com 1.240 veículos manteve contagens/quadros e reduziu 1,771 → 0,623 s sob cProfile; o tempo total desse perfil passou de 8,325 a 7,143 s. A verificação física permaneceu ativa.

No teste de fila de 300 s com demanda suficiente, a descarga por verde passou de [3,3,3] a [5,4,6], com zero colisões e zero violações da auditoria, corrigindo o problema encontrado durante a própria revisão.

As verificações finais e seus limites estão em `VALIDACAO_3_7.md`. O projeto completo e o computador do log de 40 minutos não estão disponíveis neste ambiente: não há medição que permita prometer um tempo final para esse caso. As pendências históricas de versões anteriores permanecem documentadas em `PENDENCIAS_3_6.md`; esta atualização não certifica toda a suíte histórica.
