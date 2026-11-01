# Rodovia Studio 3.0 — existente × projetado e avanço do vídeo

Revisão consolidada sobre a 2.69. Mantém o TRIM reversível e os ícones já entregues. Não modifica o DXF nem o motor de circulação.

## Uso

Em Cena → Materiais e apresentação, use **Elementos existentes no vídeo**:
- **Já exibidos desde o início** (padrão): a situação existente permanece como subcamada; o projeto surge por cima.
- **Surgir com o avanço do vídeo**: existentes e projetados acompanham a frente longitudinal.

Salve e atualize a apresentação antes de exportar. A opção permanece gravada no projeto. Salvar/descartar na janela preserva o comportamento existente do editor. A vista de edição e a captura PNG estática mostram a cena completa para conferência; a revelação temporal ocorre no MP4 e na captura de vídeo 3D.

A classe Pavimento existente e a tipologia OAE existente identificam a fase existente; nomes com EXIST/ATUAL/ANTIG identificam as demais feições. Nomes com PROJ/NOVO/NOVA/ALARG indicam projeto. Não se deduz estado pela cor. Correlações manuais de material, cores e texturas são preservadas; confira classes e nomes ambíguos no cadastro. O acostamento continua acostamento, sem virar faixa de tráfego.

## Apresentação

- Pavimento novo: tom mais escuro e uniforme; existente: mais claro, neutro e com desgaste. Mantidas as distinções de asfalto/concreto e as opções Realista/Ultra realista.
- Primeiro são compostas todas as superfícies existentes, depois todas as projetadas. Assim pavimento novo cobre o existente na coincidência, inclusive quando uma OAE existente gerava linhas por cima. O avanço primeiro mostra o existente e depois o projetado. Cotas e obstáculos físicos não são alterados por essa ordem visual.
- O mosaico, os ladrilhos de detalhe e os vetores do editor respeitam a prioridade. No 3D, uma separação visual pequena evita superfícies coplanares disputando o mesmo pixel; não altera cotas de cálculo.
- Domínio, bordos, elementos CAD, símbolos, ferrovia, sinais, veículos, pedestres e anotações projetados passam pela mesma frente de apresentação, em vez de permanecerem todos prontos no início.
- Água desenhada no CAD acompanha o projeto; a hidrografia pública e a imagem aérea continuam como contexto de fundo. O desenho derivado da análise da imagem também respeita o avanço, salvo se classificado como existente.
- Congelar uma camada protege a edição; deixa de antecipar sua apresentação no vídeo. Para exibição inicial, use a classe existente e a opção acima.
- Vídeos curtos deixam de revelar a cena inteira por uma simples transparência: têm avanço espacial. Os modos de circulação clássico e somente rota não suprimem o avanço do vídeo. As vistas de diagnóstico continuam completas.
- O avanço DXF configurado continua sendo a única antecipação intencional: contorno ligeiramente à frente da aplicação das texturas. Use 0 m para desligar.
- O último quadro conclui a revelação em vídeos curtos e capturas 3D. A sinalização e os veículos são exibidos quando a frente chega, mantendo demanda, segurança e restrições calculadas.

## Desempenho e proteções

A opção altera dependências de apresentação, sem exigir recálculo da rede por mudança de configuração. Subcamadas existentes e máscara projetada são cacheadas e compartilhadas por snapshot autenticado nos workers. Ladrilhos existentes usam cache separado e limitado. A máscara 2D consulta no máximo cerca de 33 mil pontos por pose; a máscara WebGL usa um campo limitado a 128² amostras. São aproximações de apresentação, não operações CAD nem alterações na referência de estaqueamento. Valores inválidos e caches incompatíveis são recusados.

Há memória adicional para a subcamada existente quando ela existe; não foi medido ganho ou consumo no PC Windows de 8 GB do usuário. Não é promessa de ausência universal de cintilação, homologação Windows/Defender ou conformidade normativa.

Feche o aplicativo e aplique pelo atualizador habitual, preservando projetos, imagens e vídeos. Pacote completo contém os recursos da base anterior e desta revisão; o leve exige 2.69 ou posterior. Aplicação e rollback são verificados em instalação isolada. Sem mudança na main.
