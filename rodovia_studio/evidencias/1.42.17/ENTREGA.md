# Revisão 1.42.17 — usabilidade e orientação local

36 testes direcionados aprovados, zero falhas/erros/ignorados. Incluem margens da janela Novo em 768/1024/1366 px, ferramentas sem transbordamento horizontal na aba Todas, localização de defeitos, central de recuperação, gravação real no motor, cadastro residual removido pela interface com confirmação e arquivos preservados, bloqueio de cadastro com tarefa ativa, orientação por falha real de alinhamento sem abrir modal sobre o processamento e nova criação de projeto.

Splash compilado com e sem WebView2, testado em Mono/Xvfb. Animação detectada e comparação exata dos pixels da região do logo confirmou a mesma pose inicial e final. A conclusão do splash exibe a pose inicial por 180 ms.

DXF de regressão: 31 eixos, seis fluxos revalidados, original preservado. Não é reprodução do projeto salvo atual do usuário.

ZIP aplicado sobre 1.42.16, inicialização fora da raiz e encerramento controlado aprovados. Após mover a instalação, rollback para 1.42.16 restaurou o programa byte a byte, preservando sentinelas de KMZ, cache de GeoTIFF e vídeos.

Orientação: sistema especialista local com hipóteses, passos e localização quando há ponto válido; não é modelo treinado nem diagnóstico garantido. Erros não são executados como código. A remoção de cadastro incompleto preserva a cópia em _registros_removidos e não apaga os arquivos de origem.

Validação direcionada solicitada pelo usuário; suíte integral, Windows/WebView2 nativo e uso prolongado não executados nesta revisão. Nota provisória de prontidão para uso intenso: 7/10.

Próxima revisão, conforme solicitação: evolução das camadas gráficas, fumaça ferroviária e pedestres com proteção de travessias. O protótipo arquivado de pedestres não integra este pacote.

Pacote: atualizacoes/RodoviaStudio_1_42_17_atualizacao.zip
SHA-256: f0e7e1a98fe01c4b57080218a383e7d749fcc371ef04e77a5ed8f4558dea15d1
