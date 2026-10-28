# Borda branca/preta em imagens com alfa

Falha confirmada: collar_mask ignorava toda fonte com duas/quatro bandas; sample aplicava a opção de borda somente a imagens RGB. Um RGBA com alfa 255, portanto, mantinha o colar branco opaco.

Correção: detecção também em fontes com alfa; combinar a máscara com a transparência original, nunca restaurá-la; preservar branco interno e pixels 254. Quando a máscara não está disponível, não eliminar todos os brancos da janela indiscriminadamente. Chaves de máscara e mosaico atualizadas para não reutilizar derivados anteriores; originais preservados.

Validação atual: 6 testes dirigidos aprovados (2 novos de RGBA/transparência e 4 da referência139), comparação sintética inspecionada em comparacao.png. O teste histórico de fluxo ainda usava índices posicionais; sua fixture foi atualizada para fingerprint estável da36, sem alterar o motor de tráfego.

Limites: a imagem original do caso relatado não foi fornecida nesta etapa. Isso corrige um caminho demonstrável, sem afirmar que reproduz exatamente o caso do usuário. Não é recorte destrutivo da fotografia nem corte exato universal em qualquer zoom: preserva o arquivo e gera transparência dos pixels puro branco/preto conectados à borda. JPEG quase branco, fontes float/16bits, alpha parcial, detalhes abaixo da resolução da overview e interpolação na fronteira exigem ensaios específicos. Sem novo ZIP nem exportação MP4 nesta etapa; main preservada.
