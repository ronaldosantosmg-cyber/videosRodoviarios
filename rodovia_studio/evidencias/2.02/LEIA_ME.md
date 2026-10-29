# Entrega Rodovia Studio 2.02

## Resultado

Reconstrução da trajetória inteira antes da separação de amostras inválidas, com busca limitada no corredor físico e prova de continuidade de todos os subtrechos de cada sentido. A proposta pode ser conferida, confirmada, revalidada e desfeita. Uma recusa oferece a causa e a localização quando disponível; uma recuperação parcial não libera o botão de aplicação como se fosse integral.

Permanece o motor de tráfego existente: eixos cadastrados, seções, nós, sentidos, controles, colisões e frota. A fonte CAD, recortes e desligamentos manuais são preservados. Não há novo renderizador, núcleo CAD ou modelo de IA 3B.

## Apresentação

Usar Cena → Materiais e apresentação → Maquete artística para destacar materiais e circulação. O teste desta revisão conferiu a mesma geometria de cálculo antes/depois de aplicar o perfil artístico, veículos na cena 3D e MP4 completo. Consulte FOCO_APRESENTACAO.md e entrega-validada/202_apresentacao_realista.png. O perfil existente foi validado; não foi criado um novo catálogo fotorealista.

## Validação

- Regressão integral nova da 2.02: 995 casos, inicialmente 994 aprovados e uma falha de espera no teste de fechamento do editor de hachuras (5 s). Não houve ZIP gerado nessa tentativa.
- A preparação desse teste passou a aguardar a conclusão da operação inicial antes de editar. As verificações de persistência e fechamento foram mantidas. O teste de vídeo foi ampliado para o perfil artístico.
- Revalidação: 30 casos aprovados; 965 resultados do mesmo produto foram preservados pelo verificador de hashes. Relatório consolidado: **995 testes, zero falhas, erros ou ignorados**. Não são resultados da 2.01.
- Origem, hashes, relatórios inicial/reexecutado/consolidado e imagens: entrega-final/ e entrega-validada/. Tentativas de desenvolvimento em outras subpastas são histórico, não aprovação.
- MP4 H.264/yuv420p: 1280×720, 24 fps, 72/72 quadros decodificados, sem erro de decodificação. Conferência em entrega-validada/202_rota_reconstruida_video.json.
- Inicializador C# compilado com e sem WebView2; splash conferido com Mono/Xvfb (versão, fabricante e animação). Permanece aviso CS0162 de compilação. Isso não equivale à execução nativa Windows.
- ZIP real instalado em pasta com espaços/acentos, oito arquivos alterados conferidos, snapshot/arquivamento da atualização e rollback 2.02 → 2.01 executados. Todos os hashes anteriores do programa restaurados. Configuração, KMZ, cache persistente GeoTIFF e vídeo de teste preservados byte a byte. Consulte pacote-real.json.

## Comparação e limites

O algoritmo 2.01 recusava o cenário sintético de obstáculo finito; a 2.02 encontra passagem no corredor e revalida o percurso. Medição pontual: 0,0028 s para a recusa antiga e 0,1469 s para resolver o caso novo. Não é uma comparação de velocidade equivalente nem ganho geral de desempenho.

Busca até 8 m de desvio, 20 km/20 mil vértices, 42.517 posições e 250 mil ligações por trajetória. Mantidos os limites de fontes da assistência (512 MiB/10 mil arquivos). Barreira total, informação insuficiente e auto-interseção ambígua podem exigir edição. A auditoria geométrica de referência usa veículo leve; a frota e os controles dinâmicos precisam continuar válidos. Não inventa nós ou níveis e não comprova conformidade normativa.

**Prontidão estimada: 7/10, provisória.** A reconstrução e a entrega estão mais comprovadas que na 2.01, mas faltam reprodução do projeto salvo real do usuário, homologação Windows/WebView2 no PC de 8 GB e carga prolongada. A nota não representa uma medição estatística ou garantia de corrigir qualquer desenho.

## Atualização e uso

Salvar o projeto e manter cópia. Colocar RodoviaStudio_2_02_atualizacao.zip em atualizacoes/ e usar o atualizador do aplicativo com encerramento controlado. Não apagar projetos/, videos/, originais ou cache GeoTIFF. Usar Tráfego → Corrigir problemas → Reconstruir rota completa; conferir a prévia e escolher Confirmar e aplicar correção → Revalidar resultado. Em recusa, Localizar impedimento.

SHA-256: 2654167d0fadbf9b293f15ecd8bdf89eccc19c069b137ee630f1c0863b7bc0ed. Tamanho: 12.382.573 bytes. Histórico 2.01 preservado. Publicação somente na branch de desenvolvimento; main permanece com 4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3.
