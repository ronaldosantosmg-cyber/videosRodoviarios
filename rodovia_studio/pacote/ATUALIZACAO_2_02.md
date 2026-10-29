# Rodovia Studio 2.02 — reconstrução contínua das rotas

Continuidade da 2.01, mantendo schema 31, motor existente, nós, seções, sentidos, controles dinâmicos e caminhos independentes da instalação.

## Usar

1. Atualize o diagnóstico do projeto.
2. Abra Tráfego → Corrigir problemas / Central de correção dos fluxos.
3. Escolha **Reconstruir rota completa** na origem com problema. Subtrechos da mesma origem aparecem agrupados.
4. Confira a prévia: original cinza e trajetória proposta verde. A aprovação exige um itinerário que cubra todos os subtrechos de cada sentido solicitado.
5. Use **Confirmar e aplicar correção** e **Revalidar resultado**. **Desfazer correção** restaura a configuração anterior, desde que não haja edições posteriores a preservar.
6. Se a reconstrução for recusada, use **Localizar impedimento** e a orientação. Recuperar apenas trechos válidos continua como opção avançada distinta, sem promessa de continuidade integral.

## O que mudou no motor

A reconstrução é tentada sobre a trajetória inteira antes de recortar amostras inválidas. Primeiro tenta suavização revalidada; quando necessário, busca uma passagem por estações e deslocamentos laterais no corredor físico. Toda proposta precisa passar pela conferência contínua da largura e pela análise cinemática do percurso completo. Não basta haver uma parte utilizável.

São preservados extremidades da trajetória derivada, direção, nível, origem cadastrada e fonte CAD. A entrada/saída de veículos continua respeitando o afastamento longitudinal configurado (padrão 5 m). Um itinerário não é considerado completo por somar vários itinerários desconectados. Subtrechos internos de um eixo nativo válido não são tratados como pequenas rotas independentes.

Em estudo técnico, o traçado original fica como referência cinza quando a reconstrução integral está conferida; as trajetórias revalidadas recebem as setas no sentido efetivo de deslocamento. A fonte original não é apagada.

## Proteções e limites

- Não atravessa barreiras, canteiros ou regiões excluídas para retirar avisos. Um obstáculo finito pode admitir uma passagem dentro da superfície permitida; a geometria precisa ser revisada na prévia. Não se presume conformidade de uma manobra apenas porque há espaço geométrico.
- Preserva recortes, desligamentos manuais e restrições existentes. Não cria um eixo base nem inventa nós ou níveis para ligar dados ausentes.
- Recusa auto-interseção ambígua, extremidades sem corredor contínuo e curvas reprovadas. Explica a causa e fornece ponto quando localizado.
- Limites desta busca: 8 m de desvio máximo, 20 km e 20 mil vértices por trajetória, 42.517 posições e 250 mil ligações no grafo. Buscas fora do orçamento exigem subdivisão/edição explícita.
- A auditoria geométrica de referência usa o veículo leve do modelo. A simulação e a conferência da frota continuam verificando as classes; uma reconstrução geométrica não certifica que todo caminhão/articulado caberá. Semáforos, interdições e colisões continuam no motor de simulação existente.
- Não inclui núcleo CAD completo, modelo semântico de imagens ou pesos de IA 3B. Não há promessa de corrigir qualquer desenho sem informação suficiente.

## Atualizar

Salvar e manter cópia do projeto. Colocar o ZIP em atualizacoes/ e usar o atualizador do aplicativo, com encerramento controlado. Preservar projetos/, videos/, DXF/KMZ, imagens originais e cache GeoTIFF. Conferir snapshot e rollback para 2.01.

Os testes e as evidências da revisão acompanham a entrega. Validação Linux/Mono/Chromium não equivale à homologação nativa Windows/WebView2/8 GB ou conformidade normativa.
