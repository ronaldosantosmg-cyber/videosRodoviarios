# Atualização 2.41 (não validada pelo gate completo)
# 2.41 — fluxo completo na tela, eixos não paralelos e validação com o projeto real TH53

**Projeto real TH53** (EIXO_LESTE 10.220 m, EIXO_OESTE 9.168 m, Leste = Decrescente, Oeste = Crescente): seções sobre os eixos reais, com “inverter eixo” ligado e desligado, 1 e 2 sentidos, circulam no sentido do KM (motor e rede de tráfego completa). No código 2.37 as duas saíam trocadas com “inverter eixo” ligado. Teste: `test_v14269_projeto_real_th53.py` (+ `tests/fixtures/th53_eixos_reais.json`).

**Fluxo completo na tela** (`test_v14271_fluxo_tela_completo.py`, navegador real): escolher eixo → janela Seções tipo (Adicionar seção, Salvar e fechar) → sentido Crescente no eixo → marcar “Inverter início e fim do eixo” → trocar para Decrescente → salvar → recarregar a página. Defeito encontrado e corrigido: ao marcar “Inverter eixo” a prévia das faixas NÃO mudava até recalcular (o eixo carregado na tela ainda era o antigo). Agora a prévia usa o km novo na hora (`editor.reverse_axis` x caixa marcada). Confere também o que foi gravado em disco e o que volta ao reabrir.

**Eixos não paralelos ao principal** (ramos, laços, perpendiculares; `test_v14270_eixo_nao_paralelo.py`): quando |Δ estaca| < 45% do comprimento da rota, o km não define sentido; Crescente/Decrescente passam a valer pela ORDEM DO DESENHO, igual no motor (seções e eixos nativos) e na tela. Eixos paralelos seguem o km como antes. No TH53 isto estabiliza o ramo “retorno” de 233 m (Δ estaca 36 m), que antes mudava de sentido físico ao ligar “inverter eixo”.

Não coberto: vídeo/3D renderizados, gate completo no Windows. Falhas antigas já conhecidas (test_v131 ESLint/contagens, testes de importação/visual 3D) continuam.
