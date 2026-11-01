# Atualização 2.24 (não validada pelo gate completo)

## Prévia animada dos fluxos (comando ANIMARFLUXOS, botão em "Fluxos de tráfego")
- Veículos animados sobre as trajetórias calculadas (editor.paths), direto no editor, sem gerar vídeo.
- Usa a semente (Settings.traffic_seed) e a densidade do projeto: mesma semente, mesma animação.
- Esc ou o mesmo botão param; também para ao ocultar a janela. Nada é gravado no projeto nem entra no vídeo.
- Já existente e conferido: velocidade em curva por raio (Settings.curve_speed, padrão ligado, aceleração lateral 2,2 m/s²).
- Teste: tests/test_v14252_previa_animada.py (node, sem DOM).
