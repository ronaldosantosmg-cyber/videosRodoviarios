# Evidências da revisão 1.42.28

- 203 casos únicos com último ensaio aprovado, sem ignorados. pytest-direcionado.xml e consolidacao_testes.json identificam a consolidação. Os relatórios brutos preservam falhas e retentativas; não se somaram retentativas como novos casos. Não foi executada toda a suíte histórica.
- Testes funcionais e visuais em Chromium real: hachura em projeto antigo sem origem/destino, salvar/fechar/descartar, erro de gravação preservando rascunho; API de apoio com consentimento, contrato, revisão/aplicação confirmada, erros de autenticação/limite e cancelamento.
- Transporte online simulado: não havia chave de conta para homologar um provedor real. Modelo 3B sem pesos e sem inferência real nesta entrega.
- Tráfego: diagnóstico sem mutação, exclusão de resultados obsoletos, corpo dentro da superfície, cache por posição, vista acima de 3 km, prévia em detalhe, diferença real nos pixels quando os veículos são desenhados, densidade editável e segurança de ultrapassagem. Barreiras, movimento, pare e siga e colisões cobertos pelos testes dirigidos selecionados.
- Dois MP4 de tráfego, um e dois processos: 72/72 quadros decodificados, 1280×720, 24 fps, H.264, zero erros de decodificação, veículos nas três amostras de visibilidade. Não é prova de cada veículo em cada quadro nem teste prolongado.
- DXF real TH53: original preservado por SHA-256, 31 eixos, 6 itinerários revalidados. Sete veículos ativos; um visível na vista focada de 350 m. Preparação e quadro completos em 36,89 s no ambiente deste ensaio. Não representa o projeto salvo atual do usuário nem ganho comparativo de desempenho.
- Atualização 1.42.27→1.42.28, inicialização fora da raiz, encerramento controlado, instalação movida e rollback byte a byte aprovados. KMZ, cache GeoTIFF, vídeo, perfis e relatório IA preservados. Ver verificacao_pacote.json.
- Sintaxe: 115 Python e 94 JavaScript aprovados. Auditoria estática de fontes e ZIP sem achados; isso não substitui antivírus. Iniciador compilado e splash conferido em Mono/Xvfb, não em GUI Windows.

Nota de prontidão para uso intenso: **7,5/10**, estimativa de engenharia fundamentada nos ensaios dirigidos. Pendentes: projeto salvo atual do usuário, uso prolongado/medição em seu PC Windows de 8 GB, GUI Windows completa, provedor online real e inferência 3B. Não há certificação normativa nem garantia universal contra travamentos.
