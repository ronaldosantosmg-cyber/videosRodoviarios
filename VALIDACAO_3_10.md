# Validação dirigida — Studio 3.10

Linux/Python 3.12: **81 testes dirigidos aprovados**. Ajuda e comandos conferidos no Chromium. Pacote conferido por sintaxe, manifesto, aplicação, importação, reversão, componentes e servidor real. O portão usa `--sem-suite`, pois os testes dirigidos foram executados separadamente. Não é uma promessa universal de ausência de falhas.

- Saída por chegada da frente do caminhão ao portal; nenhum corpo permanece ultrapassando o fim do traçado nas amostras; há saídas efetivas e ausência de colisões.
- Itinerário com duas arestas e conector: o veículo atravessa a conexão e só sai no extremo final.
- Obra total antes do portal: veículos a montante não atravessam a interdição por estarem próximos da saída.
- Teste geométrico com os 250 m finais de duas trajetórias exportadas pelo usuário (8 e 9), transformados de WGS84 para o CRS declarado no próprio GeoJSON. Em cada cenário isolado de 45 s, dois caminhões saíram, sem colisões nem violações da regra de ouro. São testes dos extremos reais isolados, não reprodução da rede completa ou da configuração original.
- Regressões de simulação em blocos, retomada, cache, auditoria, modo antigo e exportação MP4 verificadas. O teste de filas de semáforo continua garantindo que a exceção expire ao alcançar a via livre.

O DXF foi aberto com 12.485 entidades e unidade declarada em metros. As fontes recebidas foram preservadas e não são incluídas no pacote de atualização. Não houve renderização integral dos 220 s/6.600 quadros do empreendimento. O tempo de início no computador do usuário e a exata falha de comboio do percurso 8 não estão certificados sem sua configuração salva.
