# Atualização 2.33 (não validada pelo gate completo)
- Sentido por eixo reconstruído com FONTE ÚNICA (FLUXO em 01_estado_configuracao.js): todas as telas leem e gravam só por ela.
- Corrigido o vazamento: ao salvar, o sistema relia os seletores antigos da lista de eixos e sobrescrevia escolhas feitas em outras telas (layer, Central, Sentidos). Agora o salvar usa só cfg.route_directions.
- SENTIDOEIXO refeito: uma linha por eixo, cada um grava só a própria chave; "Definir para todos do layer" apenas preenche a tela; regras antigas por layer aparecem e podem ser removidas; chaves órfãs são limpas.
- Verificado no projeto real: inverter um eixo muda apenas os trechos desse eixo (motor); teste das 256 combinações de 4 eixos sem vazamento.
