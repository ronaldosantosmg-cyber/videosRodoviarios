# Rodovia Studio 1.40.5 — Robustez e Tráfego Pesado

## Tráfego
- Caminhões, ônibus e carretas usam dinâmica própria: menor aceleração, maior headway e maior equivalente veicular (PCU).
- Veículos leves aumentam a distância de seguimento quando o líder é pesado.
- Ultrapassagem segura existente continua respeitando os trechos permitidos/proibidos; ficar atrás de pesado aumenta a motivação para mudar de faixa, mas não afrouxa as regras de segurança.
- Capacidade nominal configurável por faixa (padrão 1900 veíc/h/faixa).
- Quando a demanda supera a capacidade, veículos aguardam na entrada; a fila descarrega conforme a faixa volta a ter capacidade disponível.
- Relatório registra fila máxima, fila atual, tempo-veículo em fila e descarga por faixa.
- O limitador preventivo de colisões da 1.40.4 permanece obrigatório.

## Salvamento e compatibilidade
- O formato/pastas de projeto permanecem iguais à versão-base 1.39/1.40.4.
- `config.json` continua no mesmo local e com o mesmo modelo.
- A gravação agora é atômica: grava temporário, força os bytes ao disco, relê/valida JSON e só então substitui o arquivo anterior.
- Falha de serialização ou escrita não destrói a configuração válida anterior.
- Salvar Como e exportar/importar pacote foram testados em regressão.

## Robustez contra falhas
- A interface é servida em módulos JS independentes. Falha de um módulo não impede o navegador de tentar carregar os demais.
- `guard()` captura ação ausente, exceção síncrona e promessa rejeitada, registra o erro e mantém a interface ativa.
- Falha ao iniciar um worker não mata o despachante de tarefas; a tarefa recebe estado `failed` e as próximas continuam disponíveis.
- O atualizador executa pré-voo antes de alterar a instalação: JSON + sintaxe Python; JavaScript também é validado com `node --check` quando Node estiver disponível.
- A entrega oficial é validada com `python -m compileall` e `node --check` em todos os módulos JS.

## Testes desta entrega
- tráfego pesado e PCU;
- formação de fila por capacidade sem colisões;
- salvamento atômico e preservação do arquivo anterior em erro;
- Salvar Como;
- exportar/importar pacote;
- carregamento modular do frontend;
- recusa de pacote com erro de sintaxe Python;
- regressão de rotas, ultrapassagem e interação.

Os testes visuais dependentes de Chromium/Playwright não puderam ser executados no ambiente de empacotamento por ausência do binário do navegador. Isso não representa uma falha funcional detectada.
