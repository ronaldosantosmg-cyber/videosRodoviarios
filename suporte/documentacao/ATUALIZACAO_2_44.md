# Atualização 2.44 (não validada pelo gate completo)
# 2.44 — frota "Rodovia brasileira realista" e motoristas com comportamento natural

Novo item em Projeto → Veículos (e em Tráfego → Frota): **Rodovia brasileira realista**. As frotas antigas continuam como estavam.

- **Frota diversa (15 classes)**: moto, hatch, sedã, SUV, picape, van, VUC, caminhão toco, caçamba, caminhão (baú), micro-ônibus, ônibus urbano, ônibus rodoviário 13,2 m, carreta e bitrem 25 m, com dimensões reais e entre-eixos próprios (colisão, curva e 3D usam as mesmas medidas).
- **Mistura**: pista principal ≈ 7% motos, 19% hatch, 18% sedã, 14% SUV, 10% picape, 3% van, 3% VUC, 3% toco, 2% caçamba, 4% caminhão, 2% ônibus, 1% micro, 2% rodoviário, 9% carreta, 3% bitrem; ramos e acessos com poucos pesados. A mistura não repete a cada 100 veículos.
- **Cores como na frota brasileira**: branco, prata, preto e cinza dominam (~80% dos carros); ônibus com várias pinturas; caminhões com cabines de cores diferentes.
- **Aparência**: SUV com rack de teto, sedã com porta-malas, hatch com traseira curta, caçamba com caçamba aberta, bitrem com dois semirreboques.
- **Motoristas**: cada um tem uma agressividade contínua (de prudente a apressado), que muda velocidade desejada, intervalo para o veículo da frente e aceleração. Pesados variam menos e respeitam o limite da própria classe. Sobre o modelo existente (IDM, troca de faixa, pré-população de 90 s), sem mudar as outras frotas.
- Teste: `test_v14275_frota_realista.py` (tabelas completas, mistura, cores, desenho de todas as classes, variação dos motoristas e simulação com ≥9 classes sem colisão). As falhas dos testes de frota/vídeo/WebGL são as mesmas da 2.40 (21 antes e depois).
- Não coberto: o 3D usa as classes-base do visualizador (carro, caminhão, ônibus, carreta) com as dimensões novas; vídeo e 3D renderizados com a nova frota não foram vistos aqui.
