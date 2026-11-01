# Rodovia Studio 2.63

Continuidade da base enviada 2.60 → 2.61 → 2.62. Não altera o motor de nós ou redefine seus fluxos.

## Atualizar

Feche o aplicativo. Guarde o ZIP em `atualizacoes/` da instalação e use o atualizador do próprio Rodovia Studio. Não copie manualmente arquivos sobre um programa aberto. O pacote leve exige 2.62 ou posterior; o completo contém todos os arquivos do programa. Projetos, vídeos e imagens persistentes ficam fora da atualização. O atualizador cria backup e oferece restauração da versão anterior.

## Usar

- **Veículos:** em Veículos e fluxo, a opção “Exibir veículos somente sobre pavimento cadastrado” exige que a carroceria inteira caiba na superfície pavimentada. Confira a classificação das hachuras: sem pavimento reconhecido, o veículo fica oculto. Este é um filtro de apresentação 2D/vídeo/3D, sem apagar rotas ou substituir a simulação física. Desmarcar recupera o comportamento visual anterior.
- **Duas seções:** Tráfego → Configurar faixas. Edite a seção existente e use “Dividir em dois trechos” na distância desejada; edite o segundo trecho e confirme. Alternativamente adicione o primeiro intervalo e use o próximo intervalo preparado. “Salvar e fechar” inclui a edição pendente. Confira o esquema e as larguras de cada lado antes de gerar.
- **Sinalização:** “Realçar pintura e sinalização na apresentação” melhora o contraste. No 3D a pintura tem largura em metros, em vez de depender de linha de um pixel. Desgaste, opacidade e mapeamentos manuais continuam aplicáveis.
- **PER Excel/CSV:** importe na janela de Obras. A prévia informa localização, trecho parcial, fora do eixo ou falta de estaqueamento. Use “Conferir posição por km” e “Localizar”. Configure o km de origem/sentido do eixo antes. A obra fora da extensão não é deslocada para a ponta do eixo; as coordenadas manuais são preservadas.

## Validação e limites

Consulte `suporte/documentacao/validacao_2_63/` no pacote e as evidências no repositório. Os testes atuais são dirigidos às alterações e dependências desta revisão. Não constituem homologação universal do legado, conformidade normativa ou validação Windows nativa. Não há substituição do motor gráfico, novo modelo IA nem certificado de assinatura de código nesta entrega.
