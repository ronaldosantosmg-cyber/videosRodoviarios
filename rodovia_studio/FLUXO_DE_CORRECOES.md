# Correções com retorno rápido

1. Reproduzir o defeito e limitar a alteração ao comportamento afetado. Registrar separadamente os pedidos da próxima revisão.
2. Executar o diagnóstico da área: `python rodovia_studio/validar_correcao.py --area popup` (também `fluxo`, `imagem` ou `interface`; aceita várias áreas). Usar `--listar` para conferir a seleção antes de executar.
3. Corrigir todas as falhas encontradas nesse diagnóstico antes de repetir a bateria completa. Resultados, capturas e os dez testes mais lentos ficam em `evidencias/<versão>/diagnosticos/<execução>/`. Uma aprovação direcionada não é aprovação para publicação.
4. Estabilizar os fontes e executar `python rodovia_studio/validar_entrega.py --gerar` uma vez. A execução reúne todas as falhas; nenhuma falha ou teste ignorado pode autorizar o pacote. Se uma falha exigir alteração, validar primeiro a área e repetir a validação final.
5. Testar atualização, encerramento, preservação de dados e rollback; publicar e conferir o download somente depois da aprovação.

Não executar baterias redundantes simultaneamente nem reiniciar uma bateria completa apenas por ajustes no plano da próxima revisão. Não reduzir verificações geométricas nem testes funcionais/visuais para diminuir o tempo. `main` permanece protegida.

Referência medida durante a 1.42.12: diagnóstico relacionado a popups/capacidade, 13 testes em 123,86 s; bateria de 439 casos em 1.390,67 s, com uma falha que levou à correção da corrida de abertura de janela durante tarefa automática. Esses tempos são referências desta máquina e desse conjunto de casos, não um prazo garantido para qualquer correção.
