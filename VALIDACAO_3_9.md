# Validação dirigida — Studio 3.9

Testes em Linux/Python 3.12 no aplicativo existente: **177 testes dirigidos passaram**, com dois testes históricos de relatório/API desmarcados. Sintaxe Python/JavaScript e ajuda no Chromium conferidas. O pacote passou pela instalação, importação, reversão, componentes e servidor real; o portão usa `--sem-suite`, pois a seleção dirigida foi executada separadamente.

- Migração das duas configurações antigas preserva rotas, demanda e semente; configurações atuais com proteções explicitamente desligadas continuam bloqueadas.
- Exportação real do modo antigo: MP4 de 3 segundos, 72 quadros integralmente decodificados, motor simulado e auditoria sem violações da regra de ouro.
- Blocos versus execução integral: estados, semente aleatória, saídas e auditoria comparados. Retomada preserva a sequência da física.
- Cache: invalidação física, reutilização visual, corrupção, aliases de controladores, instantâneos parciais e completos, limites e histórico em disco.
- Vídeo com dois processos: exportação incremental e cache completo produzem os mesmos hashes de quadros decodificados. Falha tardia remove o parcial e preserva o vídeo final anterior.

O cache não retoma a codificação do MP4. A câmera Tráfego ainda requer cálculo integral quando não existe cache compatível. A validação dirigida não encerra as pendências históricas de PENDENCIAS_3_6.md e não substitui a conferência do DXF e do projeto reais do usuário. Windows/WebView2 e o tempo total no computador do usuário precisam de verificação no destino.
