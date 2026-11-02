# Atualização 2.48 (não validada pelo gate completo)
# 2.48 — Veículos e texturas com relevo iluminado

- Veículos: desenho novo em vista superior (carroceria com volume e brilho, vidros com reflexo, teto, faróis e lanternas, rodas, retrovisores; caminhões, ônibus, carretas e motos). Cada veículo é desenhado uma vez por classe/cor/resolução e girado no quadro (rápido). SÓ aparência: a pegada cabe exatamente em L×B e as dimensões usadas nos cálculos não mudam. Se o desenho falhar, volta ao desenho simples.
- Texturas: asfalto (grão, manchas, remendos, trincas), cascalho do acostamento, grama (tufos, manchas secas), terra de corte (estratos, ravinas, pedras) e concreto (poros), com relevo iluminado. Ancoradas em coordenadas do mundo: sem costura entre ladrilhos e sem "nadar" quando a câmera anda. Opção `texture_relief` (ligada por padrão); estilo "anterior" e perfil técnico não mudam.
- Testes de exatidão: pegada, posição, rumo (inclusive tela espelhada), frente/traseira, escala, cache e queda segura; relevo sem costura, determinístico e sem alterar o tom médio.
- Inclui 2.45–2.47. Não validada pelo gate completo.
