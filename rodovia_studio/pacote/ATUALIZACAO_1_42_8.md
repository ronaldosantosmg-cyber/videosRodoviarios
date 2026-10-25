# Rodovia Studio 1.42.8

Correção dos painéis laterais e da seleção de fluxos, com reorganização da barra técnica.

Os comandos ficam agrupados por função, com títulos de grupo na aba Todas e abas próprias para Edição, Navegação, Cálculos, Estaqueamento e obras, Fluxos de tráfego, Áreas e sinalização, Tráfego e acessos, Calibração e cabine, Paisagem e Ferrovia e semáforos. Medir distância fica em Cálculos, junto da inspeção e do comando funcional de calcular/atualizar fluxos. A vista 3D fica em Navegação. Ícones distintos diferenciam mover ponto/mover objeto, alinhamento/medição, OAE/pórtico, acesso/rota e editar/incluir fluxo. A ajuda aparece por hover/foco.

- Projeto, Camadas, Propriedades, Vídeo e Mais recebem destaque conforme o painel ou menu aberto; apenas um botão fica ativo.
- O segundo clique recolhe o respectivo painel/menu. Abrir um painel principal recolhe as propriedades anteriores.
- Ativar “Selecionar e editar fluxos” limpa a seleção anterior, evitando que outro objeto intercepte o clique.
- Selecionar uma trajetória abre suas propriedades, incluindo Inverter sentido e Desativar, mesmo com o painel recolhido. Fluxos manuais continuam editáveis como geometria.

Testes em Chromium sobre a interface real verificam alternância dos painéis e segundo clique, menu Mais e seleção de fluxo sobre uma área já selecionada. A entrega exige também toda a suíte de regressão, compilação e splash pelo validar_entrega.py. Não se declara validação nativa Windows/GPU nem nova nota de prontidão; permanecem os limites da 1.42.7.

Coloque o ZIP em atualizacoes/ e aplique pelo atualizador do aplicativo. Snapshot, rollback, projetos, vídeos, KMZ e cache GeoTIFF são preservados. Main não foi alterada.


## Painéis e imagens

Os painéis abertos pelos botões laterais, pelas abas técnicas e pelos menus passam a usar uma janela ampla, com rolagem e os mesmos campos/eventos originais. A abertura não duplica nem descarta os controles. Janelas auxiliares com grades também recebem largura adaptável ao tamanho da tela.

Ao fechar com alterações, a aplicação oferece Salvar, Descartar alterações ou Continuar editando. Durante a edição, a gravação automática desses campos e o início automático de processamento ficam suspensos. Salvar confirma a configuração; falha ou conflito mantém a janela aberta. Descartar restaura configuração, marcações e histórico da abertura, preservando alterações que já estavam pendentes antes dela. Arquivos e imagens originais não são apagados. Operações de upload/importação resolvem a janela pendente antes de gravar suas fontes. Novas marcações continuam exigindo Adicionar/Aplicar antes de confirmar a configuração.

A seleção “Imagem da apresentação” fica diretamente abaixo dos menus. Permite mapa georreferenciado, somente imagem local, imagem local nos detalhes com mapa no restante da cobertura e fundo neutro. “Configurar imagens…” abre o gerenciador local e de camadas. Os modos usam os parâmetros já mantidos pelo motor aéreo/cabine, sem duplicar o GeoTIFF nem apagar o cache persistente. A seleção de cache legado só aparece em um projeto que já o utiliza.


## Histórico em caminhos longos do Windows

O temporário de gravação JSON não repete mais o nome/hash do destino. No caminho relatado, isso reduz o temporário de 289 para 223 caracteres, mantendo o arquivo definitivo com 252. O conteúdo é conferido pelo próprio descritor aberto, e a troca continua atômica. Se o temporário desaparecer, há três tentativas limitadas, com novo nome e recriação da pasta; o destino só é substituído após a conferência. Temporários ativos não são incluídos na limpeza comum de `.tmp`.

Os testes simulam o limite clássico de 260 caracteres no mesmo comprimento do relato, salvam/leem o histórico completo e simulam remoção do temporário e falha persistente, conferindo preservação do destino e limpeza dos próprios intermediários. Não foi executado OneDrive nem Windows nativo neste ambiente; a indicação de caminho longo decorre dos comprimentos medidos e da reprodução do limite no teste.
