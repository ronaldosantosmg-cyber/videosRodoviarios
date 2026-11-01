# Rodovia Studio 3.0

A aprovação desta revisão será registrada em entrega_final/resultado.json e entrega_final/pytest-resultados.xml. Os testes foram executados sobre os fontes da 3.0; não se usam resultados de versões anteriores para aprovar o produto novo.

Escopo: prioridade das superfícies projetadas sobre as existentes, cores/texturas distintas, opção persistente de existentes iniciais/progressivos, frente comum para desenho e elementos dinâmicos, remoção da antecipação por congelamento, último quadro completo em vídeos curtos, campo de revelação WebGL durante captura e restauração da edição completa após captura. Tráfego, demanda, colisões, barreiras, interdições e referências de estaqueamento permanecem calculados pelo motor existente.

Evidências: imagens 270_inicio_existente, 270_meio, 270_final e 270_existente_progressivo; comparação mosaico/detalhe/snapshot/cache; MP4 1280×720/24 fps/72 quadros decodificados; capturas reais Chromium/SwiftShader no início/fim da revelação WebGL e verificação de restauração; seleção salvar/descartar da opção; regressões de transporte, materiais, TRIM, nós, seções e atualização/rollback.

A ordem visual 3D usa um pequeno afastamento entre superfícies coincidentes. Não é alteração de cota física ou certificação de interseções em desnível. Máscaras de apresentação têm amostragem limitada e não substituem núcleo CAD. O significado existente/projetado vem da classe, da tipologia OAE e do nome da feição; nomes ambíguos exigem conferência. Personalizações de cor/material são preservadas.

Limites: testes sintéticos e regressões em Linux/Chromium; sem DXF/configuração exatos TH57, homologação nativa Windows/Defender ou medição no PC de 8 GB do usuário. A subcamada existente acrescenta memória quando necessária, com cache em disco e limites para detalhe; não se declara ganho universal de desempenho nem ausência universal de cintilação/travamentos.

Prontidão estimada: 7/10 para uso acompanhado, após aprovação final. O comportamento visual agora tem testes dirigidos, mas o projeto real e a execução Windows ainda precisam de homologação para uso intenso sem acompanhamento. A nota é julgamento de engenharia, não certificação.

ZIPs publicados somente após aprovação; integridade, aplicação/rollback e download HTTPS são registrados em pacotes-verificados.json e publicacao.json. A main deve permanecer no commit 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3.

## Numeração e continuidade

Versão 3.0 solicitada pelo usuário, consolidada sobre a base completa 2.69. As tentativas de desenvolvimento 2.70 foram mantidas para auditoria; não houve publicação de ZIP 2.70. O gate definitivo reexecuta as verificações na versão 3.0, incluindo o MP4 WebGL real e a compilação/splash com o número novo. O limite curto é 360 s para esta matriz com duas exportações reais; falhas, erros ou ignorados continuam bloqueando o empacotamento.

Guia para outra IA: rodovia_studio/CONTINUIDADE_3_0.md. Branch desenvolvimento/rodovia-studio-3.0; não fazer merge na main.

A tentativa entrega/ terminou com 171 aprovados e uma falha na seleção de referências para DXF adiantado; nenhum ZIP foi gerado. A classe domínio foi mantida fora da antecipação DXF, preservando sua apresentação normal quando habilitada. A execução entrega_final/ valida a correção.

## Resultado aprovado

172 testes reexecutados e aprovados na 3.0 final, zero falhas, erros ou ignorados. Tempo total do gate: 312.65 segundos; é tempo da infraestrutura de validação, não benchmark no PC do usuário. Sintaxe Python/JavaScript, splash e compilação C# com/sem WebView2 aprovados. O pacote só foi gerado nessa execução aprovada.
