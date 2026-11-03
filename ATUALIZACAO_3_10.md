# Rodovia Studio 3.10

Correção da saída da frota no aplicativo existente. Instale pelo atualizador e reinicie o Studio.

O fim do itinerário completo funciona como um portal de retirada: o veículo deixa a simulação quando sua frente chega ao extremo. Antes, aguardava que o centro alcançasse um limite quase no fim do traçado; o corpo ainda podia ocupar a região terminal e interferir em outras reservas. A retirada usa o comprimento da classe do veículo e os recuos do portal. Conexões intermediárias continuam sendo percorridas.

Semáforos, pedestres, obras e reservas de segurança antes do portal permanecem ativos. Não são apagados veículos no meio da pista para esconder congestionamentos. As violações da regra de ouro continuam bloqueando a exportação.

O diagnóstico de comboios agora inclui instante da simulação, causa, folga, velocidade, líder e distância restante até a saída. A mensagem de erro mostra os principais dados, e a auditoria guarda o restante.

O cache é invalidado pela mudança do código físico; a primeira geração desta revisão precisa recalcular o tráfego. Gerações posteriores com física compatível reutilizam o cache validado. Resolução, FPS, superamostragem e encoder continuam configuráveis e não foram reduzidos.

## Desempenho e limites

Um vídeo de 220 s a 30 FPS possui 6.600 quadros. O perfil Final usa superamostragem e aumenta o custo da montagem. A aceleração do encoder não acelera automaticamente geometria ou física. Esta correção não comprova a eliminação da espera inicial no empreendimento completo.

DXF e GeoJSON fornecidos foram lidos. A exportação GeoJSON contém geometria em WGS84 e indicação de origem EPSG:31983; não contém toda a configuração de demanda, controles e rede da simulação. Trajetória numerada na exportação não equivale necessariamente ao índice do itinerário combinado usado no erro. A reprodução integral do percurso 8 continua dependendo da configuração salva do projeto.

Consulte [a validação](VALIDACAO_3_10.md). A ajuda explica a saída terminal e sua diferença em relação à ocultação visual fora do pavimento.
