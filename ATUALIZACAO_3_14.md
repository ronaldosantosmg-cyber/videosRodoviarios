# Rodovia Studio 3.14 — nascimento seguro da frota

Atualização do aplicativo existente. Instale pelo atualizador e reinicie.

## Correções

- A semeadura considera veículos de outros itinerários que já ocupam a mesma pista, inclusive através de uma conexão interna. A posição só é admitida quando há folga à frente e atrás.
- O índice espacial existente é atualizado a cada inserção. Não se constrói nem se ordena a ocupação global a cada candidato. O alcance da consulta acompanha a velocidade e o comprimento dos veículos.
- A entrada contínua também respeita a folga mínima fora das filas, inclusive em baixa velocidade. A demanda pendente aguarda a admissão segura.
- A orientação da regra de ouro passa a indicar distribuição inicial, espaçamento, mudanças de faixa, retenções e confluências, conforme o caso. A simples presença das palavras “pedestre” e “vídeo” na mensagem não provoca mais o diagnóstico genérico de travessia/FFmpeg.
- Configurações que exigem o motor simulado recebem orientação própria. Erros reais de pedestres e encoder mantêm suas orientações.

Não se corrige uma folga inferior a 12 m apenas zerando a velocidade. O motor evita a posição inválida antes de inserir o veículo. Nenhum veículo já em circulação é apagado para esconder o problema.

A quantidade inicial pode ser menor do que a soma pedida por percursos sobrepostos; eles não representam várias pistas independentes. O relatório mostra recusas por espaçamento compartilhado. As chegadas continuam na taxa configurada, sujeitas à capacidade e à segurança.

A regra de ouro, a validação das prévias e a auditoria de exportação permanecem ativas. Não foram adotados os atalhos de ignorar violações nas prévias ou silenciar indiscriminadamente os avisos do DXF. O bloco indevido de pintura 3D citado no texto anterior já havia sido retirado na 3.13.

[Validação](VALIDACAO_3_14.md).
