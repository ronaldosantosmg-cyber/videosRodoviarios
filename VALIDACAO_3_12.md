# Validação — Studio 3.12

Linux/Python 3.12, Node e Chromium.

- Rodada ampla: 116 testes aprovados, incluindo vídeo, simulação, cache, taludes DXF, zebrados, vazios e materiais.
- Conferência final: 23 testes aprovados após o acabamento final, incluindo independência entre estilos e exportação Full HD com superamostragem. São testes parcialmente sobrepostos à rodada ampla.
- Artístico não chama a camada de fissuras/remendos realistas; a opção realista continua chamando sua própria camada.
- Taludes mantêm as cores por tipo, cobertura texturizada e vazios. No artístico natural, linhas internas de offsets não sobrepõem a superfície nem preenchem vazios.
- Alternância de estilos com cache: bases e ladrilhos têm assinaturas distintas; ao retornar ao artístico, sua base correta é recuperada. Trilhas de desgaste ficam exclusivas do realista.
- Chromium: paleta e textura dos taludes, cor manual, vazios e mapas 3D distintos ao alternar artístico/realista; o mapa correto é reutilizado ao voltar ao estilo anterior.
- Prévias Full HD dos dois estilos produzidas com o DXF e configuração fornecidos. O quadro artístico foi inspecionado: pavimento e pintura legíveis, superfície avermelhada do corte sem os traços técnicos grossos. As imagens e configurações privadas não foram incluídas no repositório.

A referência guiou as texturas e o acabamento. A geometria, materiais cadastrados e sinalização seguem os dados de origem. As prévias do projeto usam fundo neutro, pois os arquivos locais de imagem/satélite do Windows não foram fornecidos. O vídeo integral de 220 s/6.600 quadros não foi codificado nesta validação. Pendências históricas não relacionadas não são encerradas por esta revisão.
