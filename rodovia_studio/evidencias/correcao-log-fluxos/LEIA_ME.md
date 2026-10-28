# Correção dos logs de fluxo, assistência e imagem combinada

Código de desenvolvimento sobre 1.42.36. Não é ZIP instalável nem homologação Windows. Relatórios intermediários preservados; resultado.json usa a última execução de cada caso sem somar repetições.

## Correções

- Leitura/gravação UTF-8 explícita na assistência, no pedido do worker e nos resultados do diagnóstico. Teste usa o padrão cp1252 simulado e caracteres que antes falhavam. Não equivale a executar o aplicativo nativo no Windows.
- Prévia sem alvo de tráfego publica vista geral e editor para permitir correção. Não muda câmera/configuração persistida nem reativa eixos. Vista explícita não chama a câmera de vídeo antes de usar seu próprio enquadramento.
- Exportação com veículos ativados e sem itinerários não publica um vídeo vazio como sucesso. Diagnóstico consultável mesmo após recusa, associado à configuração/revisão; resultado antigo não é atribuído a uma configuração nova. Vídeo anterior preservado.
- Aviso ENSAIO sai dos pixels do vídeo; fica na janela de avisos e nos metadados. Descrição informa exatamente as opções ativas. Nenhuma proteção foi reativada ou desativada para esconder o aviso.
- Em imagem combinada, falha de rede no mapa permite usar imagem local válida sobre fundo neutro fora da cobertura. Erro continua nos avisos. Imagem fora da área ou arquivo inválido não são tratados como cobertura válida. Rede real não foi usada nos testes: fonte web e indisponibilidade foram simuladas.
- Polígonos KML não são linhas/eixos. Seu volume não consome o orçamento de coordenadas das linhas utilizadas; limite do XML, arquivos e validação de DTD permanecem. Linhas acima do limite continuam exigindo divisão. Hachuras CAD também não viram eixos.
- Perfil padrão reconhece HATCH_PAV_NOVO, HATCH (pista) e variantes de pavimento existente, incluindo EXITENTE. Projeto com mapeamento manual precisa revisar/aplicar a sugestão; o perfil não sobrescreve decisões manuais automaticamente.
- Pincel descarta respostas atrasadas após Esc, mudança de contexto/modelo ou solicitação mais recente.
- Diagnosticar veículos oferece acesso a pavimentos/hachuras, sentidos/nós e modo de ensaio/proteções.

## Evidência no DXF disponível

Arquivo TH53 anteriormente fornecido, SHA-256 7936e09e195212a85a894dbc48f5ad337f0cbe4f3195225e6f8137297e3e4538. O arquivo fonte foi preservado. Com mapeamento explícito obtido do perfil anterior: 0 itinerários; 17 trechos com corpo fora do pavimento reconhecido; superfície reconhecida 61.552,6 m². Com as regras de nomes corrigidas: 7 itinerários; relatório de 46 veículos simulados e 5/4/5 ativos nas amostras de 0/1,5/2,9 s; superfície 173.630,5 m². Outros trechos continuam recusados. dxf-real.json detalha as condições.

Esse ensaio não reproduz a configuração salva do usuário: ela não veio com o log. Usa cadastro explícito derivado do perfil, sem confirmação de CRS. Não autoriza liberar todos os trechos nem certifica velocidades, normas, capacidade ou ausência universal de colisões.

## Testes e limites

Há exportações reais H.264, decodificação integral, 1280×720, 24 fps, 72 quadros por vídeo, incluindo imagem local + web simulado e indisponibilidade de rede. Capturas foram inspecionadas. Em dois casos iniciais de imagem combinada, o teste alterava o objeto de configuração compartilhado antes de exportar; corrigido para usar uma cópia e repetido. A fixture antiga de capacidade não cadastrava o eixo: corrigida para exercer a política atual sem alterar o motor. Outra falha inicial alterava editor.json sem renovar sua proveniência; corrigido o arranjo do teste.

A suíte histórica completa permanece sem aprovação de entrega, conforme a tentativa anterior bloqueada em evidencias/1.42.37. Não foi gerado ZIP novo, nem repetida homologação nativa Windows/8 GB, instalação ou rollback nesta etapa. Prontidão global mantida em 7,8/10, condicionada a projeto real e regressões de entrega. Main preservada.
