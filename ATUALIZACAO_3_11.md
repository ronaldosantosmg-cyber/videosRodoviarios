# Rodovia Studio 3.11

Correção do aplicativo existente, após reprodução com DXF e configuração enviados pelo proprietário. Instale pelo atualizador e reinicie o Studio.

## Causa confirmada do comboio

A falha original foi reproduzida exatamente: percurso 8, posição 8.232,35 m, aos 174 s. Com essa configuração o itinerário mede 9.145,41 m; a falha ocorre cerca de 913 m antes do fim, e não no portal de saída. A alteração terminal da 3.10 não resolvia essa ocorrência.

O veículo 67 saía da faixa aos 160 s, iniciava o retorno aos 170 s e concluía aos 174 s. A folga de 29,219 m a 56,27 km/h ficava abaixo dos dois segundos exigidos pela auditoria. O motor não acompanhava o líder do destino no IDM durante a troca completa; a reserva física evitava colisão, mas não assegurava a folga de apresentação.

## Correções

- Previsão da folga de chegada na faixa, à frente e atrás, considerando velocidade relativa e duração da troca. Manobras sem folga aguardam outra oportunidade.
- Enquanto troca de faixa, o IDM considera o líder mais restritivo entre origem e destino.
- Fora das filas autorizadas, a distância de parada do IDM passa a respeitar o mínimo de 12 m da auditoria, com margem numérica de 0,5 m. Antes buscava distâncias menores, produzindo outro bloqueio aos 186,4 s no teste intermediário.
- A origem das filas semafóricas é propagada considerando também a folga de parada livre, sem estender a exceção para veículos já livres a jusante. A descarga por verde permanece validada.
- O cache de geometria aceita a largura interna já validada da cena Final (2.880 para saída 1.920), mantendo a validação das resoluções recebidas externamente. A superamostragem não muda a geometria nem o editor.

Não foram desligadas ultrapassagens, colisões ou auditoria. A frota aguarda quando a troca não é segura. Os resultados físicos anteriores são invalidados pela assinatura do código. FPS, resolução e qualidade permanecem os configurados.

[Validação e limites](VALIDACAO_3_11.md).
