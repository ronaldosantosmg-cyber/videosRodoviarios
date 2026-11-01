# Atualização 2.28 (não validada pelo gate completo)

Versão única com correções e melhorias (cumulativa, inclui 2.17–2.27).

**Correções**
- Faixas de sinalização sumidas no editor 2D: a textura da 2.26 era pintada por cima; agora é pintada por baixo das linhas e setas.
- Sentido do EIXO_OESTE: novo sentido por layer (comando SENTIDOEIXO), que vale para todos os eixos do layer e sobrevive à troca do DXF; a escolha individual de um eixo continua valendo mais. O motor avisa quando uma escolha salva não casa com nenhum eixo atual.
- 168 `catch` vazios do JavaScript passam a registrar o erro (`RodoviaErros`, comando DIAGNOSTICOJS).
- 69 `except: pass` do Python passam a registrar a falha (`app/falhas.py`), sem mudar o comportamento.
- 11 leituras/gravações de JSON com UTF-8 explícito; proteção contra trajetória de 1 ponto no tráfego.

**Aparência**
- Asfalto novo (CBUQ): ligante preto-azeviche, agregado britado claro e uniforme, tom uniforme; asfalto existente neutro com grão fino.
- Canteiro: grama com relevo de tufos iluminado pela posição e altura do sol, sombra entre tufos e resposta ao clima (chuva, nublado, neblina), usando as opções de clima e hora do sol.
- Concreto sem "nuvens"; OAE com barreiras New Jersey vistas de cima (topo claro, face sombreada, sombra), juntas de dilatação com chapa metálica e tabuleiro em cinza de pavimento.
- Editor 2D: texturas ao vivo realistas (asfalto novo, grama, terra, concreto) que reagem aos ajustes de textura.

**Recursos**
- Estilos de mapa 2D (comando ESTILOMAPA: Técnico, Maquete, Satélite) e minimapa do traçado (comando MINIMAPA).
- Paleta de comandos Ctrl+K, escala e seta do norte.

**Testes**
- Testes de navegador têm o marcador `navegador`. Gate rápido: `pytest -m "not navegador"`.
- Testes novos: texturas, canteiro/clima, sentido por layer. Três testes antigos ajustados (seção no bordo, textura artística, clima).
- Gate por arquivo no ambiente de análise: cerca de 60 testes antigos de motor ainda falham (ver relatório); não foram causados por esta versão, mas não foram corrigidos.

**Pendentes**: assistente de interseção, fase/fila de semáforo, demanda por ramo nas setas, linha cinza fantasma, gate completo no Windows.
