# Pendências verificadas na revisão 3.6

Consulta ao GitHub em 02/11/2026: nenhuma issue aberta. Os workflows Linux e Windows da 3.5.1 concluíram com sucesso. Isso não significava aprovação da suíte histórica inteira.

O arquivo original `suporte/sistema/tests/linha_base_falhas.txt` contém 179 identificadores de falhas históricas. Ele foi preservado; esta entrega não transforma essas falhas em aprovação.

Uma varredura parcial de testes sem navegador, executada antes das correções, terminou com 152 aprovações e 16 falhas. Doze das falhas já constavam da lista histórica; quatro não constavam. A execução foi interrompida, portanto não cobre o restante da suíte. Os testes dirigidos da 3.6 são registrados em VALIDACAO_3_6.md.

## Corrigidos nesta entrega

- `test_traffic_hydro::test_no_turn_at_grade_separated_crossing`: conexão incompleta podia derrubar o cálculo com KeyError; agora é recusada sem inventar conexão.
- `test_v14239_conflict_guard::test_guarda_resolve_sobreposicao_quando_as_outras_barreiras_falham`: o teste de falha não gerava a sobreposição que pretendia verificar depois da semeadura da 3.5. O cenário passou a desligar explicitamente semeadura e equalização de velocidades, mantendo o teste efetivo da guarda. Nenhuma proteção do produto foi retirada.
- O teste de orçamento de processos foi atualizado para a divisão real de CPU entre montagem e FFmpeg e passou a especificar os recursos simulados, sem depender da máquina que executa o teste.
- Foram adicionadas verificações de estabilidade do canvas, conservação dos quadros, reserva geométrica, invalidação de cache, instante de prévia, orçamento de CPU e MP4 integralmente decodificado.

## Ainda precisam de triagem/reprodução

| Grupo | Casos observados | Situação |
| --- | --- | --- |
| Eixos, retornos, recortes e continuidade | `test_right_hand_traffic_and_connected_return`, `test_network_only_recovers_when_explicitly_requested_and_respects_disable`, dois casos de `test_v14210_flow_tools`, quatro de `test_v14213_continuity`, `test_small_nodes_are_removed_only_from_derived_path_and_old_disable_stays_valid` | Divergências de itinerários/identidade nas expectativas antigas. Verificar cadastro, autorização e tolerâncias atuais; não liberar tráfego inválido para fazer um teste passar. Um caso compara estritamente comprimento maior que 510 m com resultado 509,9999999999998 m. |
| Materiais | `test_wheel_paths_on_existing_pavement_detail`, `test_natural_earthworks` | Divergências de máscara e cor em relação às expectativas históricas. |
| Imagem combinada + tráfego | dois parâmetros de `test_mixed_imagery_exports_decoded_video_with_vehicles_and_no_trial_banner` | Cenário não encontrou veículos desenhados; exige conferir o cadastro e a configuração de câmera atuais do fixture. |
| Pare e siga | `test_pare_siga_never_reverses_while_tail_is_in_shared_corridor` | Não registrou colisões traseiras, mas a quantidade de mudanças de fase foi menor que a esperada. Isso não encerra a análise funcional da travessia. |
| Compatibilidade histórica | `test_recovery_configuration_can_be_read_by_the_previous_release` | Exige o ZIP 1.42.9, ausente; não há evidência para afirmar essa compatibilidade. |
| Fixture de vídeo antigo | `test_workflow::test_video_encoder` | Não autoriza explicitamente um eixo e a versão atual bloqueia o vídeo quando veículos estão ligados sem itinerário. O novo teste de MP4 usa eixo autorizado e decodifica todos os quadros. |

As linhas acima são pendências de verificação, não uma lista de defeitos confirmados em qualquer projeto. Desempenho integral no computador do usuário, projeto/configuração atual, Windows/WebView2 e GPU física continuam exigindo validação no alvo. Os resultados sintéticos não substituem essa validação.
