# Ícones InfraRail — 1.42.11

O pacote de 32 símbolos SVG fornecido pelo usuário está incorporado localmente em `app/icons/infrarail-sprite.svg`. O arquivo original foi preservado byte a byte (SHA-256 `a54a83c01a61d34d60706f0d761e7d2226f36ba86dc9ebefd81989a72745e9dc`). Nenhuma fonte ou biblioteca externa é necessária.

Os ícones aparecem nos comandos técnicos correspondentes: apagar intervalo, juntar subsegmentos, nova rota, sentido, ferrovia, semáforo, OAE, edificações e vegetação. As propriedades usam os símbolos de recuperação e sentido único/duplo. O catálogo de materiais inclui simbologia de redes, gás, hidrologia, erosão, cortina atirantada, fibra, radar e torre. A iluminação 3D alterna os símbolos de dia/noite. O diálogo ferroviário usa silhuetas distintas para carga e passageiros.

Os nomes acessíveis, ajuda por hover/foco, agrupamento e ações existentes são mantidos. SVGs são decorativos, sem capturar o mouse. Símbolos sem um comando correspondente permanecem disponíveis no sprite: não criam recursos novos, não identificam modelo físico específico de locomotiva e não alteram geometria, tráfego ou texturas do vídeo.

A página incorpora os símbolos uma única vez, antes dos módulos. `RodoviaInfraRail.icon(nome)` gera um uso local pelo identificador; `forTool(id)` e `forMaterial(classe)` mapeiam funções existentes. Nomes inválidos ou ausentes retornam vazio e os comandos mantêm seus ícones anteriores quando não há equivalente.

Para instalar a atualização, coloque o ZIP em `atualizacoes/` da instalação e utilize a atualização do Rodovia Studio. Os pacotes históricos são preservados.
