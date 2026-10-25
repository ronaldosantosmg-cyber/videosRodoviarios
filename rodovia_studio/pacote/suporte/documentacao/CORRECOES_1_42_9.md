# Revisão 1.42.9

- Confirmação dos dados dos painéis antes de iniciar cálculos: salvar, descartar ou continuar editando. O comando continua após a confirmação.
- Conversão de imagem publica a referência sobre a configuração mais recente; a interface recebe a nova revisão sem perder edições locais ou o histórico de desfazer. Conflitos exigem escolha explícita.
- Inventário de camadas disponível antes da análise, incluindo camadas nomeadas em blocos e camadas vazias. Lista de classificação e gerenciador usam o mesmo inventário. Classificação de uma camada original continua válida após sua divisão por cor e tipo.
- Diagnóstico de rota explica tratamento automático e revisão manual. Geometria original e desativações manuais são preservadas. Não constitui certificação de conformidade normativa.
- Interrupção da captura do mouse restaura a geometria anterior do arraste e libera o cursor.
- Teste de criação e reabertura parte de um navegador vazio. Teste de conversão utiliza GeoTIFF válido previamente registrado no cache; não simula suporte nativo ECW indisponível.
- Diagnóstico curto: `python validar_entrega.py --rapido`. Não gera pacote nem substitui a validação completa. Entrega: `python validar_entrega.py --gerar`, após todas as verificações obrigatórias.

## Limites da validação

Windows/WebView2, OneDrive e o conversor DWG instalado no computador do usuário não foram executados nativamente neste ambiente Linux. O sucesso em arquivos sintéticos não comprova todos os projetos. A avaliação de campo informada pelo usuário para a 1.42.7 permanece 2/10; não há fundamento para declarar prontidão de 9,5/10.
