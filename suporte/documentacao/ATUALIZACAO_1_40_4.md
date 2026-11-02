# Rodovia Studio 1.40.4 — Simulação de Tráfego

## Objetivo
Transformar o movimento de veículos em microssimulação: a animação recebe apenas estados validados pelo motor de tráfego.

## Segurança física
- IDM continua controlando aceleração/frenagem em seguimento.
- Antes de cada avanço existe um **limitador preventivo**: o veículo não pode avançar além do espaço livre até o veículo líder.
- Uma segunda barreira numérica corrige qualquer sobreposição residual antes do quadro ser gravado.
- Veículos em mudança de faixa reservam simultaneamente a faixa de origem e a de destino.
- O relatório inclui colisões, menor gap, intervenções de segurança e manobras bloqueadas.

## Mudança de faixa e ultrapassagem
Cada `route_alignment` possui uma política:
- `off`: não muda de faixa;
- `marked` (padrão): só muda em trechos explicitamente **permitidos**;
- `safe`: pode mudar salvo trechos explicitamente **proibidos**.

A manobra:
1. só ocorre entre faixas adjacentes do mesmo alinhamento e mesmo sentido;
2. exige gap seguro à frente e atrás na faixa de destino;
3. só é iniciada quando traz ganho real sobre o veículo líder;
4. valida **toda a distância da transição**; se qualquer parte interceptar trecho proibido, é cancelada;
5. é interpolada lateralmente de forma contínua durante 4 s — sem salto instantâneo.

## Curvas e raios
Curvatura pode reduzir a velocidade do veículo para manter a animação estável, mas o Rodovia Studio **não altera a geometria nem o raio**. Incompatibilidades geométricas permanecem diagnóstico técnico para decisão do usuário.

## Interface
Nas propriedades da rota foi acrescentado **Ultrapassagem e mudança de faixa**, com:
- política da rota;
- tabela início/fim;
- regra Permitida/Proibida.

O padrão é conservador: um projeto sem zonas cadastradas não inventa ultrapassagens.

## Compatibilidade
- Rotas antigas continuam válidas: o campo novo assume `marked` e, sem zonas permitidas, não faz mudança de faixa.
- O modo de tráfego antigo continua disponível conforme as opções existentes.
- Nenhuma geometria original de DXF/DWG é regravada pelo simulador.
