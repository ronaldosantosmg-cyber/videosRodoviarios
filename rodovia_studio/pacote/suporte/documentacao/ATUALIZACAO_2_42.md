# Atualização 2.42 (não validada pelo gate completo)
# 2.42 — corrige falha ao gerar vídeo (pickle da cena)

Erro: `AttributeError: Can't get local object 'make_chain.<locals>.<lambda>'` em `Scene.snapshot` (render.py). Causa: a cadeia de km criada na 2.39 (`routes.make_chain`) era uma função lambda guardada na rede de tráfego, e o snapshot da cena para o vídeo usa pickle. Correção: `make_chain` devolve um objeto (`_KmChain`) serializável, com o mesmo cálculo.

Teste novo (`test_v14270_eixo_nao_paralelo.py`): a cadeia faz pickle ida e volta; uma cena com tráfego grava o snapshot e recarrega. Defeito introduzido na 2.39 e não pego antes porque os testes de rota/fluxo não gravavam o snapshot de uma cena com tráfego.
