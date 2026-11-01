# Rodovia Studio 2.08

**Estado: NÃO validada pelo gate nem em Windows/WebView2. Testes de geometria escritos e não executados (sem shapely/pytest no ambiente de montagem).** Cumulativa sobre a 2.07.

## Mudança
- Túnel ou trecho longo sem hachura/pavimento: se o eixo continua e o pavimento volta depois, o fluxo **não é mais cortado**, qualquer que seja o comprimento (limite técnico 5 km, configurável até 50 km em `traffic_bridge_max_m`). Os veículos somem 5 m antes do trecho e reaparecem ao voltar o pavimento.
- A opção “🚧 Ocultar o fluxo onde faltar pavimento” agora vem **ligada por padrão**; desmarque para voltar ao comportamento anterior (fluxo cortado nos vazios).

Instalação e rollback como nas versões anteriores.
