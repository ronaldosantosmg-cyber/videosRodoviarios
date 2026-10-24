# Rodovia Studio 1.42.6

## Ferrovia

Modelar → Ferrovia e semáforos → Ferrovia. Crie o alinhamento por pontos (Enter conclui) ou selecione uma linha do DXF. Nas opções também pode usar um alinhamento editável selecionado. O original não é alterado. Botão direito na ferrovia → Propriedades: carga/passageiros, fluxo ativo, sentido, linha simples/dupla, bitola, velocidade, intervalo e semente.

Locomotiva mais mínimo/máximo de vagões ajustáveis entre 5 e 100, inclusive; mínimo não pode superar máximo. Limites iguais produzem composição fixa. O sorteio é determinístico pelo projeto/semente/passagem. Linha simples nos dois sentidos alterna as passagens; linha dupla usa vias separadas. O intervalo mínimo é ampliado para a composição máxima desocupar o alinhamento.

Passagens no mesmo nível bloqueiam os veículos antes dos trilhos, com aviso antecipado inclusive para o próximo ciclo antes de o trem entrar no alinhamento, e liberam somente após o último vagão e a margem de segurança. Veículos não entram na passagem se a fila à frente não oferecer espaço de saída. O aviso é ampliado para veículos lentos e cruzamentos oblíquos. Coincidências ou encontros quase paralelos entre ferrovia e trajetória rodoviária no mesmo nível bloqueiam os veículos e geram aviso para revisão, sem apagar o original. Trechos em níveis lógicos diferentes não recebem esse bloqueio. Nível lógico não comprova cota real ou gabarito.

## Semáforos

Clique o centro do cruzamento e informe direções dos eixos A e B (B vazio = A+90°, editável para cruzamentos oblíquos) e número de faixas transversais a atravessar por A e B. Dois tempos SEM faixa de pedestres: verde de cada movimento = 2×n+5 segundos. Três tempos COM faixas e fase exclusiva de pedestres: 2×n+15 segundos; fase de pedestres usa o maior n. Há amarelo de 3 segundos e limpeza de pelo menos 12 segundos, ampliada para largura/velocidade. A limpeza é adicional ao verde. O motor impede entrada no cruzamento sem espaço de saída.

Link de onda verde: clique origem e destino; velocidade define deslocamento por distância entre centros / velocidade. Não admite ciclos, destinos duplicados nem planos incompatíveis. Os links são de estudo e não aparecem no vídeo. Propriedades do link pelo botão direito na linha. A onda verde depende do alinhamento, sentidos e demanda; não garante passagem sem retenção.

Lastro, trilhos, dormentes, faixas, trens, faróis e luzes aparecem na apresentação aérea, na vista WebGL e na cabine. A câmera da cabine respeita os controles e o veículo à frente. Alterações exigem atualizar os fluxos / a prévia; cenas antigas são invalidadas. A prévia WebGL continua limitada a 60 s: uma composição longa pode não passar inteira dentro dessa janela. O MP4 aéreo/cabine pode usar duração maior. Todos os vagões existem mesmo quando estão fora da área enquadrada.

## Importação, seleção e tráfego

KMZ: os 100 MB se aplicam ao XML KML processado, não às imagens anexas. Os anexos ficam preservados no ZIP e não são extraídos pelo leitor geométrico. Mantém limite de upload de 400 MB, limites de XML/coordenadas/entradas e rejeição de caminhos inseguros, senha, DTD, XML e coordenadas inválidas. Mensagens distinguem causas. Uma importação recusada preserva o arquivo anterior e a análise carregada. O KMZ TH53 original não foi fornecido; não se declara que seu conteúdo específico foi reparado.

Seleção de fluxo: tolerância em pixels ajustada ao zoom, com limite de alcance, mensagem de fluxo ausente/desatualizado separada de clique fora da linha. Atualizar fluxos não exige gerar vídeo.

Capacidade nominal admite valores positivos até 20.000 ucp/h/faixa, inclusive 3.500, como parâmetro de cenário; isso não prova capacidade física nem aprovação normativa. Demanda explícita positiva até 20.000 veíc/h/faixa substitui a densidade automática. Zero, negativos, vazios obrigatórios e não finitos são recusados. Itinerários da mesma entrada compartilham demanda e capacidade. O relatório informa equivalências internas e indicativo de sobressaturação/F, sem classificar A–E nem certificar DNIT/HCM. Nível de serviço F não tem um limiar universal de 3.500 veículos/h/faixa.

A consulta ao manual oficial DNIT foi bloqueada pela rede (HTTP CONNECT 403). O domínio www.gov.br foi acrescentado ao rascunho de rede; requer revisar/salvar e publicar o ambiente para efetivar. Nenhuma tabela DNIT foi incorporada ou apresentada como verificada.

## Atualização e limites

Coloque o ZIP em atualizacoes/ e use a atualização do aplicativo. Mantém snapshots/rollback, projetos, vídeos, KMZ e cache persistente de GeoTIFF. main preservada.

Simulação ilustrativa, sem certificação ferroviária, CONTRAN, DNIT/HCM ou validação de gabaritos/entrevias. A apresentação 3D não substitui projeto geométrico, estudo de sinalização ou programação semafórica de campo. Windows/WebView2/GPU nativos e carga prolongada permanecem pendentes.
