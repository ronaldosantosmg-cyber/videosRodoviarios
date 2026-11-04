# Rodovia Studio 3.22 — comboio como aviso e juntas de pavimento

## Retirada do bloqueio por comboio

Por solicitação do proprietário, aproximações/ comboios deixam de lançar a exceção que interrompia o vídeo. A decisão foi retirada de `app/fleet_policy.py`, função `require_export`, usada pela preparação, checkpoints e exportação. Trocar somente `simulation.py` não retirava essa decisão.

O diagnóstico original é preservado com percurso, estação, instante, folga e veículos envolvidos. No modo normal, os veículos não são ocultados por essa ocorrência. A opção voluntária de ocultar itinerários com alertas permanece disponível e identificada como operação parcial.

Colisões físicas, simulação incompleta e configurações incompatíveis continuam impedindo a exportação. As reservas de movimento e a admissão segura da 3.19 permanecem ativas. Não se cria uma causa de controle fictícia, não se apagam ocorrências nem se removem veículos para liberar o vídeo.

O valor cadastral `traffic_export_scope=strict` foi mantido por compatibilidade; nesta versão corresponde a registrar avisos e manter veículos. A interface e a ajuda deixam de dizer que esse modo bloqueia por comboio.

Essa alteração remove o bloqueio de exportação. Não é uma afirmação de que a causa física de todo comboio em qualquer projeto foi eliminada. O caso informado pelo proprietário (135,37 m; 202 s; folga 8,088 m) permanece como evidência para revisão do comportamento do motor.

## Texturas

Mantidas as escolhas anteriores: artístico como padrão, realista separado, pavimento rígido com juntas orientadas pelo eixo, OAE com detalhes próprios e taludes sem material de pista.

Corrigida uma inconsistência da representação por placas: o espaçamento entre juntas longitudinais ficava fixo em 3,5 m. Agora o mosaico e os ladrilhos de detalhe usam `lane_width_m`, incluindo a fase quando a referência é o centro da faixa. Contornos, vazios e geometria DXF não são alterados.

Não há nova etapa de aquecimento ou passagem de simulação. A saída visual de 25 m no fim do itinerário é preservada.

## Atualização

O ZIP mantém o perfil de produção da 3.21, sem testes de desenvolvimento. A situação de homologação do antivírus continua pendente; esta revisão não declara o alerta anterior resolvido.

Aplicar pelo atualizador existente. Para instalações compatíveis 3.18–3.21, `fleet_policy.py` é o arquivo central da mudança de decisão de exportação; o pacote completo também atualiza textos, ajuda e a correção das juntas.

Consulte [a validação](VALIDACAO_3_22.md).
