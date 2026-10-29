# Foco: materiais da via e circulação

A 2.02 acrescenta reconstrução contínua ao motor existente. O perfil Maquete artística já existente foi exercitado com essa reconstrução, sem substituir o motor gráfico nem alterar a fonte técnica.

## Uso recomendado

1. Confira a escala, os eixos cadastrados, os sentidos, as seções e a classificação das áreas. Esses dados técnicos continuam sendo a base dos cálculos.
2. Em Cena → Materiais e apresentação, escolha **Maquete artística**. Confira o material da área selecionada e os mapeamentos manuais; salve as escolhas.
3. Em Tráfego → Corrigir problemas, proponha **Reconstruir rota completa** quando houver defeito geométrico. Confira a proposta antes de confirmar e revalidar. Um impedimento físico real exige localização e tratamento, não liberação forçada.
4. Gere uma prévia curta e confira pavimento, acostamento, canteiro, OAE e veículos antes da exportação final. A classificação e a largura precisam corresponder ao projeto.
5. O estudo técnico serve à edição e ao diagnóstico. As linhas coloridas de diagnóstico não são materiais da via nem devem compor o vídeo final.

## Evidência desta revisão

O teste test_reconstructed_route_reaches_actual_3d_and_decoded_video usa o perfil artístico com materiais naturais, textura artística e qualidade aprimorada. Compara as trajetórias com a geometria de cálculo anterior à mudança de aparência, verifica veículos na cena 3D e decodifica o MP4 inteiro. A fonte DXF é preservada.

- Imagem: entrega-validada/202_apresentacao_realista.png.
- Conferência: entrega-validada/202_rota_reconstruida_video.json.
- Cenário sintético de 300 m com defeitos geométricos; não substitui testar o projeto salvo do usuário.

A revisão não acrescenta um novo catálogo de materiais ou um renderizador fotorealista. Mantém as opções de apresentação dos projetos existentes; não as sobrescreve silenciosamente. O enquadramento mostrado na evidência usa os títulos e anotações já disponíveis no aplicativo. A qualidade visual precisa continuar sendo avaliada em cenas reais; não há equivalência demonstrada com Twinmotion.
