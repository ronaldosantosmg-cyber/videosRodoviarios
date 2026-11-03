# Validação — Studio 3.13

Linux/Python 3.12, Node e Chromium.

- Rodada ampla: 123 testes aprovados, incluindo vídeo, cache, simulação, materiais, taludes, zebrados e vazios.
- Conferências dirigidas: 28 testes de concreto, rocha, estilos, DXF e exportação aprovados; testes parcialmente sobrepostos à rodada ampla.
- Nomes explícitos e substituição manual: CORTE ROCHA recebe rocha; CORTE SOLO permanece solo. A escolha manual pode trocar qualquer uma dessas associações.
- Mosaico e ladrilho de detalhe distinguem rocha e solo, sem preencher vazios. A máscara de rocha reaproveita a rasterização limitada ao retângulo de cada polígono e respeita sua união.
- A rocha tem textura determinística em coordenadas do projeto; pixels fora da sua máscara permanecem intactos.
- Concreto artístico mais claro, com juntas dentro do polígono. A paleta da opção realista continua separada.
- Cena 3D e vetores 2D preservam o material. A rocha não é confundida com grama ou solo e o pavimento rígido recebe a paleta clara.
- Conferência final dos materiais: seis testes aprovados, incluindo MP4 HD de 3 s/24 FPS com 72 quadros integralmente decodificados.
- Chromium: padrões de concreto e rocha, vazios, cores, taludes e alternância de estilos verificados.
- O DXF fornecido contém 19 superfícies fechadas identificadas na camada F-HZ-CORTE ROCHA. Foram geradas prévias dos acabamentos do modelo com fundo neutro, sem publicar os insumos privados.

As amostras públicas são imagens dos shaders do aplicativo, geradas por `scripts/amostrar_materiais_referencia.py`, sem recortes da fotografia nem geometria do projeto. Não foi reconstruído o relevo da foto e não foi codificado o vídeo integral de 220 s nesta revisão. As pendências históricas não relacionadas permanecem registradas.
