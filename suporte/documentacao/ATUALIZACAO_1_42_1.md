# Rodovia Studio 1.42.1

Continuidade do pacote 1.42 recebido e conferido por SHA-256. Esta revisão não altera a branch main.

- Propriedades abre e recolhe no segundo clique. Redimensionar o editor preserva o painel correto de objeto, fluxo, ligação ou geometria DXF.
- Menu principal em cascata, navegação por setas/Enter/Esc, grupos de Modelar e menus de contexto conforme a seleção ou o comando ativo.
- Comandos, opções da ferramenta, mini-barra da seleção e linha de comando ficam abaixo do menu, fora da tela gráfica. Painéis continuam encaixados.
- Fluxos: verde para itinerário calculado, vermelho para problema/desativado e amarelo para ajuste ou recálculo pendente. O diagnóstico usa a rede calculada; não certifica condições reais da rodovia. As linhas técnicas não são desenhadas no vídeo.
- A API de atualização entende o formato atual de candidatos. Somente atualizacoes/ é monitorada. Pacotes inválidos vão para rejeitadas e os aplicados são arquivados, sem sobrescrever arquivos de mesmo nome.
- Snapshot completo e manifesto persistidos antes da primeira substituição; falha de atualização restaura automaticamente os arquivos anteriores. O rollback valida caminhos e hashes antes de escrever e também possui snapshot de recuperação. Na próxima abertura, trocas interrompidas são recuperadas.
- Diretórios com espaços, acentos e instalação movida são cobertos pelos testes. Projetos, vídeos, KMZ e a base persistente de GeoTIFF ficam fora dos destinos da atualização e do rollback.
- Encerramento controlado com token da sessão, salvamento confirmado, adiamento em caso de comando incompleto, erro ao salvar ou tarefa ativa. O iniciador fecha sua janela incorporada e seu servidor; não encerra Edge/Chrome do usuário.
- Splash com versão 1.42.1, fabricante Ronaldo Santos e logo animado. Corrigido suporte ao fundo transparente do controle do logo.
- Rasterio declarado como dependência do processamento de ortomosaicos. Reforçados testes numéricos que antes capturavam também suas próprias falhas de asserção.

Antes da primeira transição, salve e feche a 1.42. Depois de aplicar a revisão, execute sistema/COMPILAR INICIADOR.cmd com o aplicativo fechado para ativar o iniciador 1.4. O iniciador antigo não recebe comportamento novo apenas pela troca dos arquivos Python/JavaScript.

Consulte validacao_1_42_1/resultado.json no pacote gerado para os resultados desta entrega. Testes históricos em outros documentos pertencem às versões indicadas. A validação atual é Linux/Chromium/Mono; execução nativa do PowerShell e WebView2 no Windows não foi realizada nesta máquina.
