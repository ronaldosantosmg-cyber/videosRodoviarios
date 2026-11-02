# Atualização 2.30 (não validada pelo gate completo)
- Central do projeto (CENTRAL): leitura única de entradas/derivados/resultados, limpeza por projeto ou novo DXF com backup e desfazer.
- app/seguro.py: divisão/raiz/log/média protegidos contra zero, infinito e vazio; 60 divisões críticas protegidas; erros 422 amigáveis.
- Tela Seções/pare-e-siga: motivo real do erro ao salvar + pré-checagem (exige uma faixa por sentido).
- Tela Sentidos das vias e nós: alterações agora mudam o fluxo (política única de sentido).
- Propriedades: campos internos (source, source_axis_*) somente leitura, para evitar edição que travava a tela.
- Gate por arquivo: 58 falhas antigas (antes 61), nenhuma regressão nova.
