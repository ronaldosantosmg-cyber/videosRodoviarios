# Rodovia Studio 2.09

**Estado: NÃO validada pelo gate nem em Windows/WebView2. Testes de geometria/tráfego escritos e não executados (sem shapely/pytest no ambiente de montagem); apenas a lógica pura (`signal_timing.py`) e a parte JS foram executadas.** Cumulativa sobre a 2.08.

## Correção
- **APARAR:** nas versões 2.06–2.08 o atalho `TR` colidia com `TR` (Trecho da rota): o comando duplicado interrompia o script e o botão ✂ não aparecia. Agora o APARAR usa `APARAR` e `TRIM`; `TR` volta a ser Trecho. Teste de contrato impede comandos duplicados e aliases novos.

## Pare e siga inteligente (obras em pista simples)
- Verde **mínimo**, verde **máximo** (antes: tempo fixo), prolongamento enquanto há fila no sentido liberado, troca ao esvaziar (gap-out) e **vermelho geral** após o último veículo sair do trecho. Nunca troca sem demanda no sentido contrário; nunca inverte com veículo dentro do trecho.
- Demanda = veículos a até 120 m do portão. Formulário: Verde máximo, Verde mínimo, Vermelho geral e a opção “Inteligente” (ligada por padrão; desmarque para o comportamento anterior de tempo fixo).

## Semáforos
- **Amarelo calculado pela velocidade** (reação 1 s + v/2a, entre 3 e 6 s). Antes era 3 s fixos, insuficiente a 60 km/h (3,8 s). Opção `signal_amber_auto` (ligada). Vale para o relógio, os veículos, os pedestres e o 3D.
- `signal_timing.py`: vermelho geral por geometria, verde de pedestres (7 s + travessia/1,2 m/s), escoamento de fila e auditoria que compara o que o semáforo tem com o exigido.

## Já existia e foi conferido
Fase exclusiva de pedestres (semáforo de 3 fases): veículos param no vermelho e pedestres só iniciam a travessia se houver tempo; faixa sem fase de pedestres fica em espera com aviso.

## Ainda não feito
Auditoria dos tempos exibida na tela; pedestres em semáforo de 2 fases; regra de obras além do pare e siga; os itens abertos da 2.07.
