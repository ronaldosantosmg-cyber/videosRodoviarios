# Rodovia Studio 1.28 — seleção e comandos aplicados ao modelo, menus que somem ao concluir

## Problemas corrigidos
- **Alterações perdidas:**
  - **Antes:** enquanto uma tarefa rodava (análise, atualização automática dos fluxos, prévia), o servidor recusava salvar a configuração. Ao terminar a tarefa, o editor recarregava o projeto do disco e a edição feita nesse intervalo **sumia**.
  - **Agora:** a configuração é salva mesmo com tarefa em andamento (a tarefa já tinha lido a configuração ao começar). Antes de recarregar, o editor grava o que estiver pendente.
- **Desfazer e seleção:** recarregar o mesmo projeto ao fim de uma tarefa não apaga mais o histórico de desfazer nem a seleção.
- **Menus que não sumiam:**
  - o menu do botão direito agora fecha quando se clica na tela (antes, clicar sobre um objeto com o menu aberto o deixava na tela);
  - a **mini-barra** fica escondida durante um comando.
- **Ao concluir um comando, a seleção é limpa, como no CAD:** grips, mini-barra e painel somem. Vale para mover, girar, copiar, escala, espelhar, paralela, copiar propriedades, trocar textura e trocar nome. Arrastar com o mouse mantém a seleção, para continuar ajustando.
- **Pedido do comando:** aparece também na área de mensagens (por exemplo, “GIRAR — ponto base: (Enter conclui · Esc cancela)”). Antes aparecia só na linha de comando e parecia que o comando não tinha feito nada.

## Alterações refletidas na prévia e no vídeo
- **Com a prévia renderizada à vista** (*Fundo de edição: Prévia renderizada*), toda alteração **refaz a prévia desta vista sozinha**, 2,5 s depois da última mudança. Se houver outra tarefa rodando, a prévia espera ela terminar. Pode ser desligado em “Atualizar a prévia desta vista ao alterar”, no painel de propriedades.
- **Com a imagem web à vista,** o editor já mostra as alterações. Uma faixa amarela avisa que a prévia renderizada está desatualizada, até você clicar ⟳ Regenerar prévia.
- **Vídeo:** sempre usa a configuração salva. O botão Gerar salva antes de começar.
- **Áreas com textura própria:** aparecem no editor com a indicação “🖌 textura própria”.

## Medido neste ambiente
- **Testes:** **246 testes automáticos passaram** (245 da 1.27 + 1 novo). O teste novo roda no Chromium e confere:
  - girar pelo menu (o pedido aparece na mensagem; ao concluir, seleção e mini-barra somem; o valor é salvo);
  - o menu fecha ao clicar na tela;
  - **arrastar uma placa durante a análise:** a posição é salva e continua depois que a tarefa termina, e o desfazer é mantido;
  - **com a prévia à vista:** uma alteração refaz a prévia sozinha e o fundo continua na prévia.
- **Testes anteriores ajustados ao novo comportamento:** depois de COPIAR, a seleção é limpa; o teste seleciona as cópias de novo antes de GIRAR.
- **Regressão TH57:** idêntica à 1.27 (nada mudou na geração das imagens).

## Não verificado / limitações
- **Windows:** não testado no seu computador.
- **Tempo da prévia automática:** depende do tamanho da vista e do computador; no TH57 inteiro, a prévia pode levar dezenas de segundos.
- **Duas janelas abertas:** se as duas editarem o mesmo projeto ao mesmo tempo, vale a última gravação.
