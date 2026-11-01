# Rodovia Studio 2.67 — entrega

Base efetiva: desenvolvimento/rodovia-studio-2.66, commit 6d4946c. Trabalho exclusivo na branch desenvolvimento/rodovia-studio-2.67; main preservada em 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3 (conferir valor exato em verificacao de publicação).

## Resultado

Comandos ZEBRADOBRANCO / ZEBRADOAMARELO e ícones compactos em Cena. Contorno reutiliza a ferramenta existente; Enter abre a janela com cor, largura, intervalo livre, inclinação por fluxo próximo ±45° ou ângulo manual, amostra, confirmação e cancelamento. A referência automática recusa ambiguidade, fluxo desligado ou distância superior a 50 m. O ângulo fica gravado, não muda com pan/zoom.

Corrigida a prévia técnica que usava diagonais em pixels, ignorando os parâmetros físicos. Barras novas têm fase ancorada no mundo. Valores inválidos, contornos cruzados e áreas acima do orçamento são recusados. Áreas antigas conservam os padrões anteriores até serem editadas. O WebGL recebe pinturas preenchidas da mesma coleção do vídeo, preservando furos e letras separadas.

Não foram alterados traffic.py, simulation.py ou routes.py. Teste confirma trajetórias iguais antes/depois de acrescentar zebrado. A pintura é representação; não cria regras novas de bloqueio de veículos.

## Evidências

final/resultado.json: 100 testes passados, zero falhas, erros ou ignorados; suíte em 101,67 s e gate total 110,94 s, com dois processos isolados. Compilação C# e splash em Mono/Xvfb passaram. Execução inicial interrompida para corrigir anéis separados de letras no 3D não gerou pacote; o resultado válido é o de final/.

267_zebrado_ui.png e 267_zebrado_render.png foram inspecionados visualmente. Teste adicional de compatibilidade do zebrado legado: 1 passou (legado-zebrado.log). MP4 da revisão decodificado com dimensões, fps e 72 quadros conferidos, além dos vídeos dos perfis existentes. Sem medição comparável de ganho de desempenho do aplicativo; tempo de gate não é desempenho de uso.

pacotes-verificados.json: atualização real de instalação isolada 2.66, conferência de arquivos, rollback e preservação byte a byte de projetos, KMZ, GeoTIFF e vídeo, nos dois ZIPs. Pacote leve recusa base inferior à exigida.

## Pendências e prontidão

Parâmetros iniciais de projeto ajustáveis, não certificação CONTRAN. O portal oficial gov.br foi bloqueado pela política de rede; conferência de aplicação, dimensões e inclinação no MBST volume IV continua pendente. Não houve teste nativo Windows/WebView2/Defender ou ensaio prolongado; não se declara ausência universal de falhas.

Nota de prontidão: 7/10 para uso acompanhado. O recurso novo tem validação funcional e visual, mas distribuição intensa exige ensaios Windows e validação de projetos reais variados. A revisão 2.65 externa não fornecida não foi incorporada.
