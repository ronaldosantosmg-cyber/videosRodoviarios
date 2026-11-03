# Validação 3.16

- 20 testes passaram: isolamento de alinhamento local com inversão geral ligada/desligada, alinhamentos secundários maiores que o principal, alteração de sentido e desativação de um secundário sem mudar outro, promoção explícita com serialização, herança de km, prévia, uniformidade dos sentidos e preservação dos vínculos.
- Reproduzido com o DXF TH53 e o config.json mais recente fornecidos: referência CAD de 10220,32 m; fluxos nativos e classificação idênticos com alinhamento local normal, invertido e removido. Os insumos originais não foram modificados.
- Uma verificação adicional (`test_v14268_apresentacao_segue_km`) falhou na concordância entre setas e arestas. A mesma falha foi reproduzida carregando a implementação anterior de geometry.py, confirmando pendência preexistente. Não foi ocultada nem alterada a expectativa do teste.
- A validação desta revisão não inclui vídeo completo, Windows ou avaliação visual integral da sinalização. A recusa geométrica do percurso Leste continua exigindo correção própria.
