# Vídeos Rodoviários

Projeto para geração automatizada de vídeos técnicos rodoviários a partir de arquivos **DXF + KMZ/KML**.

## Objetivo do MVP

Fluxo inicial:

1. carregar DXF e KMZ/KML;
2. validar os arquivos;
3. identificar geometria e referências principais;
4. preparar a cena-base;
5. gerar uma prévia;
6. renderizar um vídeo MP4.

## Princípios

- aplicação genérica para diferentes trechos rodoviários;
- mínimo de configuração manual;
- sem dependência obrigatória de InfraWorks, QGIS ou Blender;
- módulos independentes para geometria, câmera, tráfego, chamadas e renderização;
- logs claros e testes automáticos antes de novas versões;
- compatível com Windows sem necessidade de privilégios administrativos sempre que possível.

## Estrutura

```text
src/videos_rodoviarios/
  core/       # modelos e regras centrais
  io/         # leitura DXF/KMZ/KML
  geometry/   # classificação e tratamento geométrico
  render/     # prévia e vídeo
  ui/         # interface

tests/        # testes automatizados
.github/      # validação contínua
```

## Estado atual

Fase 1: estrutura-base e validação de entradas.

Próxima etapa: implementar leitura robusta de DXF/KMZ e geração da primeira prévia visual.
