# Validação 3.19 — regra de ouro e custo de processamento

Ambiente Linux/Python 3.12. Medianas de três execuções da física, sem codificação MP4, no mesmo ambiente. Variações pequenas não constituem promessa de ganho no computador do usuário.

## TH53 real, regra estrita e 220 segundos simulados

| Configuração | Densidade | Antes (s) | Depois (s) | Variação |
|---|---:|---:|---:|---:|
| TH53 recente, 2 itinerários | 1 | 1,225 | 1,156 | −5,6% |
| TH53 recente, 2 itinerários | 4 | 1,666 | 1,635 | −1,9% |
| TH53 anterior, 9 itinerários | 1 | 14,054 | 14,277 | +1,6% |

Nessas execuções: zero colisões e violações; mesmas contagens de entradas/saídas antes e depois (46/45, 78/74 e 118/54). Não foi usado modo parcial nem filtro visual para liberar a auditoria física.

Nessas redes específicas não há confluência indexada nos primeiros 120 m das entradas. Isso verifica que a proteção não interfere nos percursos fora de seu alcance, mas não prova sua atuação. O caso seguinte exercita efetivamente a retenção.

A condição adicional TH53 anterior/densidade 4 teve mediana anterior de 67,635 s. Não foi repetida depois nesta rodada; não se usa esse número para alegar comparação de desempenho.

## Confluência curta com retenção efetiva

Cenário sintético, 80 s, densidade 4, semente 2, geometria e regra iguais, comparação com o novo controle ligado/desligado apenas no processo de teste:

| Aquecimento configurado | Sem controle (s) | Com controle (s) | Violações antes/depois |
|---|---:|---:|---:|
| 0 s | 0,394 | 0,277 | 2 / 0 |
| 10 s | 0,494 | 0,331 | 2 / 0 |

Com a proteção, 58/67 tentativas foram retidas e 13/16 veículos saíram; nenhum foi removido para esconder falhas. As consultas a vizinhos foram 132/152. As contagens variam porque o controle altera o momento de entrada e a evolução do tráfego; essa medição não é garantia de aceleração geral. O aquecimento foi mantido em 0/10 s, sem acréscimo.

O risco adicional encontrado foi a entrada de um veículo na ligação compartilhada enquanto outro permanecia parado perto do fim do acesso lateral. Apenas comparar tempos de chegada ignorava a folga traseira desse veículo parado. O controle agora exige essa reserva antes da admissão.

## Regressões

55 testes distintos aprovados nesta revisão. O conjunto principal passou com 52 testes; o arquivo de admissão foi depois ampliado e executado separadamente com 11 aprovações, das quais 8 já pertenciam ao conjunto anterior.

Testes de admissão verificam retenção/liberação, veículo parado, manutenção das posições existentes, ausência de controle fictício, consulta local com fila de 10 mil elementos, ausência de consultas em trecho sem confluência, conservação das contagens, saídas efetivas e regra estrita com três sementes e aquecimentos 0/10 s.

Também foram executados os testes de confluências, admissão espacial, semeadura compartilhada, troca de faixa, saídas, filas de semáforo, inicialização, cache/checkpoints, preparação e exportação MP4 de 192 quadros com dois processos, leitura do vídeo e preservação do arquivo anterior em falha física.

Dados: [desempenho.json](https://github.com/ronaldosantosmg-cyber/videosRodoviarios/blob/main/validacao/3.19/desempenho.json). Reprodução do caso sintético: `python scripts/medir_admissao_confluencias.py` no ambiente de desenvolvimento com dependências de teste existentes. O script desliga a proteção somente na instância temporária de comparação; não altera configurações salvas ou o aplicativo instalado.

## Limites

É um controle local complementar, não garantia universal de ausência de erro. A auditoria continua bloqueando conflitos reais. Não foi medido o tempo de um vídeo completo de 220 s nesta revisão. Windows/WebView2 e encoder/GPU do usuário não foram executados aqui. A suíte histórica integral não foi executada; são mantidas as ressalvas documentadas na 3.18. Não houve dependência nova nem alteração das premissas de alinhamento, sentidos ou materiais.
