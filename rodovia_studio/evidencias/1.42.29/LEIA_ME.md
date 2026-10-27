# Evidências da revisão 1.42.29

- 123 casos únicos com último ensaio aprovado, sem ignorados; consolidação pelo início de cada suíte, com relatórios brutos preservados. A primeira janela de 3 segundos não continha manobra ativa: o ensaio de vídeo foi ampliado para 12 segundos e passou sem retirar a exigência de observar o afastamento.
- Sondagem: saída suave e retorno; limite de 1 m além do bordo; hachura de acostamento larga não amplia esse limite; recusa por barreiras, vazios/canteiros, espaço insuficiente, obras e pedestres. Entrada de pesado impedida se já houver pedestre ocupando seu corpo. Passarelas em nível separado preservadas.
- Simulação real de encontro de pesados em rede genérica: corpos, folga lateral de 0,30 m, sinais de saída/retorno e contadores de colisão conferidos. Histórico de múltiplas manobras preservado para reproduzir posições já validadas.
- MP4 de sondagem: 288/288 quadros decodificados, 1280×720, 24 fps, H.264, sem erro de decodificação. O ensaio força frota pesada somente por fixture; o mix do produto não é alterado. Ver video_sonda.json e imagem 14229_pesado_sonda_acostamento.png.
- Regressões dirigidas de semáforos/ferrovia, interdições/pare e siga, pedestres, movimento, seções, interface, diagnóstico de veículos e snapshot autenticado. MP4 com um/dois processos nos testes de regressão; não se certifica toda a frota em cada quadro nem uso prolongado.
- Chromium real: opção salva/desligável e interface em diferentes tamanhos. Iniciador e splash compilados/conferidos em Mono/Xvfb; isso não equivale à GUI Windows.
- DXF real TH53 preservado por SHA-256: 31 eixos, seis itinerários revalidados, sete veículos ativos e um desenhado na vista de 350 m. Ensaio neutro HD/2048; preparação e quadro em 42,82 s neste ambiente. Não é medição comparativa controlada nem validação do projeto salvo atual do usuário.
- Atualização 1.42.28→1.42.29, inicialização fora da raiz, encerramento controlado, instalação movida e rollback byte a byte aprovados. KMZ, GeoTIFF, vídeos, perfis e relatórios preservados. Ver verificacao_pacote.json.
- Sintaxe e pacote verificados via validar_entrega.py; auditoria estática de fontes e ZIP sem achados. Auditoria estática não substitui antivírus.

## Limites

A interpretação implementada é o afastamento local para abrir espaço em encontros e acomodar o corpo em curvas. Não se criou uma faixa contínua nem ultrapassagem longitudinal pelo próprio pesado através do acostamento. A largura cadastrada do acostamento é independente do envelope excepcional.

Frota mantida: corpo rígido conservador, carreta de 18,6 m; não há dinâmica articulada homologada de 30 m, conformidade CONTRAN certificada ou garantia universal de ausência de travamentos/colisões. A suíte histórica completa não foi executada.

Prontidão estimada para uso intenso: **7,5/10**, baseada nos ensaios dirigidos. Pendentes uso prolongado no PC Windows de 8 GB do usuário, GUI Windows completa, calibração de frota e projeto salvo atual. A main não foi alterada.
