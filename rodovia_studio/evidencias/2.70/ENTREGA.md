# Rodovia Studio 2.70

A aprovação desta revisão será registrada em entrega/resultado.json e entrega/pytest-resultados.xml. Os testes foram executados sobre os fontes da 2.70; não se usam resultados da 2.69 para aprovar o produto novo.

Escopo: prioridade das superfícies projetadas sobre as existentes, cores/texturas distintas, opção persistente de existentes iniciais/progressivos, frente comum para desenho e elementos dinâmicos, remoção da antecipação por congelamento, último quadro completo em vídeos curtos, campo de revelação WebGL durante captura e restauração da edição completa após captura. Tráfego, demanda, colisões, barreiras, interdições e referências de estaqueamento permanecem calculados pelo motor existente.

Evidências: imagens 270_inicio_existente, 270_meio, 270_final e 270_existente_progressivo; comparação mosaico/detalhe/snapshot/cache; MP4 1280×720/24 fps/72 quadros decodificados; capturas reais Chromium/SwiftShader no início/fim da revelação WebGL e verificação de restauração; seleção salvar/descartar da opção; regressões de transporte, materiais, TRIM, nós, seções e atualização/rollback.

A ordem visual 3D usa um pequeno afastamento entre superfícies coincidentes. Não é alteração de cota física ou certificação de interseções em desnível. Máscaras de apresentação têm amostragem limitada e não substituem núcleo CAD. O significado existente/projetado vem da classe, da tipologia OAE e do nome da feição; nomes ambíguos exigem conferência. Personalizações de cor/material são preservadas.

Limites: testes sintéticos e regressões em Linux/Chromium; sem DXF/configuração exatos TH57, homologação nativa Windows/Defender ou medição no PC de 8 GB do usuário. A subcamada existente acrescenta memória quando necessária, com cache em disco e limites para detalhe; não se declara ganho universal de desempenho nem ausência universal de cintilação/travamentos.

Prontidão estimada: 7/10 para uso acompanhado, após aprovação final. O comportamento visual agora tem testes dirigidos, mas o projeto real e a execução Windows ainda precisam de homologação para uso intenso sem acompanhamento. A nota é julgamento de engenharia, não certificação.

ZIPs publicados somente após aprovação; integridade, aplicação/rollback e download HTTPS são registrados em pacotes-verificados.json e publicacao.json. A main deve permanecer no commit 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3.

## Numeração final

O usuário solicitou a versão 3.0. A execução entrega_final/ desta pasta foi interrompida para renumerar o produto. Nenhum ZIP 2.70 foi publicado. Somente evidencias/3.0/ aprova os fontes, versão e pacote efetivamente entregues como 3.0.
