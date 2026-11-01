# Rodovia Studio 2.12

**Estado: NÃO validada pelo gate completo nem em Windows/WebView2.** Cumulativa sobre a 2.11 (a atualização manual do usuário ainda não foi recebida).

- Pulo da imagem (vídeo de tela): a barra da seleção (▦ ✎ ⠿) aparecia e sumia na faixa de comandos e empurrava o mapa ~40 px. Agora reserva a altura (invisível quando oculta).
- “Padrão da classe” vazio: novos materiais para bordo, barreira, canteiro, terrapleno, faixa de domínio, pintura horizontal, corte e aterro (não mudam o padrão das classes existentes).
- Fluxo: a ponte de vão sem pavimento NÃO atravessa canteiro/barreira real (impedimento físico continua cortando). Teste de contorno e obstáculo volta a passar.
- Testes de motor: corrigidos fixtures antigos (eixo precisa estar cadastrado na classe Eixo). Suíte filtrada de tráfego/fluxo/camadas: 260 passaram, 46 falharam e 37 erros (navegador) antes das correções desta versão; falhas restantes listadas abaixo não foram resolvidas.

Pendentes conhecidos: 4 testes em test_v14213_continuity; ~40 falhas em outros testes de fluxo (fixtures sem eixo cadastrado, a confirmar); testes de navegador não executáveis aqui; textura ao vivo ao selecionar layers; painel por eixo; instalador/MP4 não verificados.
