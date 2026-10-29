# Reconstrução 2.02 — método e comprovação

O motor existente continua responsável pelos eixos, seções, nós, sentidos, fontes, barreiras, canteiros, OAE, interdições, semáforos, frota e vídeo. A alteração reconstrói a trajetória derivada e não modifica a fonte CAD.

## Diferença observável

Cenário sintético: eixo reto de 300 m, pavimento de 20 m de largura e obstáculo finito interceptando o traçado. Comparação com o código extraído do ZIP 2.01:

| Versão | Reconstrução integral | Resultado |
|---|---|---|
| 2.01 | Não | Recusava porque o eixo original interceptava a região não permitida |
| 2.02 | Sim | Busca no corredor encontrou passagem, preservou extremidades e revalidou o percurso completo |

Tempos de uma execução Linux: 0,0028 s para a recusa antiga e 0,1469 s para a reconstrução nova. Não é um ganho de velocidade: a nova versão executa trabalho adicional que antes não existia. Não extrapolar para DXF grande, FPS interativo ou Windows/8 GB. Dados em comparacao-reconstrucao.json.

## Processo

1. Verificar geometria, origem cadastrada, estado atual e desligamentos.
2. Tentar reconstruir a trajetória inteira antes de recortar suas amostras inválidas.
3. Tentar suavização revalidada; se necessário, buscar passagem por estações e deslocamentos laterais no corredor físico permitido.
4. Manter progressão e extremidades; revalidar simplicidade, largura contínua e cinemática.
5. Exigir um itinerário que cubra todos os subtrechos de cada sentido da origem. Não somar itinerários desconectados para declarar sucesso.
6. Mostrar a proposta isolada, confirmar a aplicação e revalidar a simulação/frota. Desfazer usa a revisão anterior e recusa sobrescrever edições posteriores.

A busca é limitada a 8 m de desvio, 20 km/20 mil vértices por trajetória, 42.517 posições e 250 mil ligações no grafo. As propostas mantêm ainda os limites preexistentes da assistência: 512 MiB de fontes e 10 mil arquivos. Modelos fora desses limites precisam de subdivisão ou edição explícita.

A superfície permitida e os sentidos cadastrados são as referências do modelo. Espaço geométrico não comprova legalidade de uma manobra; a proposta precisa ser revisada. Não são criados nós ou níveis para adivinhar conexões ausentes. Auto-interseções ambíguas são recusadas.

## Casos acrescentados

- Passagem válida ao lado de obstáculo finito, nos dois sentidos.
- Vários defeitos fora da superfície no mesmo traçado.
- Barreira total recusada sem recuperação parcial disfarçada de reconstrução.
- NaN, infinito e comprimento nulo recusados.
- Itinerários separados não contam como um percurso integral.
- Reconstrução da rede antes da separação de amostras inválidas.
- Preservação de recorte e desligamento manual.
- Subtrecho interno nativo abaixo do limite independente continua integrado ao eixo.
- Prévia real, aplicação, revalidação e desfazer, com fonte CAD preservada.
- Percurso reconstruído na cena 3D e em MP4 de 72 quadros/1280×720/24 fps decodificados.
- Proposta bloqueada com causa/ponto; tentativa de aplicar recusada.
- Interface real: Aplicar desabilitado, Localizar impedimento centraliza a barreira e mantém acesso à central.
- Aviso em geometria já contínua não permite uma marca de correção sem efeito.

Os testes finais exigem a regressão completa do produto 2.02. Resultados da 2.01 não aprovam a alteração nova. A tentativa de desenvolvimento em entrega/ foi interrompida para acrescentar a proteção contra propostas sem efeito; permanece apenas como histórico.

## Limites da conclusão

A auditoria geométrica de referência usa o veículo leve do modelo; a simulação/confêrencia de frota continua recusando classes incompatíveis. A aprovação geométrica não assegura passagem de qualquer caminhão/articulado e não é conformidade normativa. Não foram executados o projeto salvo específico do usuário, carga prolongada no PC de 8 GB ou Windows nativo.
