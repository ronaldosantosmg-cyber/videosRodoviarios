# Entrega 1.42.4

219 testes aprovados, sem falhas, erros ou ignorados. Python e JavaScript
validados; interface Chromium e capturas inspecionadas; vídeo MP4 integralmente
decodificado. Compilação C# com e sem WebView2 e splash animado via Mono/Xvfb
aprovados. O servidor gráfico da primeira tentativa foi reiniciado e a validação
completa foi repetida antes de gerar o ZIP. Permanecem os avisos conhecidos de
depreciação de TestClient e compilação condicional C# sem WebView2.

## Alterações entregues

- Barra compacta completa de comandos da 1.39 imediatamente abaixo dos menus.
  Mostrar nomes eliminado; ajuda por hover/foco. Referência ZIP recebida idêntica
  à usada nos testes, SHA-256 a3cfbbf7b71dd11b391fc170cde108d609642f778ec0aa91bab46fe30a082bba.
- Limite por projeto de 20 em 20 m até 200 m, mais padrão 50 m. Filtro de fontes
  manuais e derivadas, preservando geometria e bloqueios manuais. Atualização
  automática ao alterar seleção quando não há tarefa em andamento.
- Zoom normalizado, maior aproximação e proteções numéricas; desfazer/refazer
  invalida caches, não para em estados sem alteração e limita o histórico.
- Fontes locais incluídas com licença; diagnóstico local de dependências e FFmpeg.
- Snapshots da configuração/entradas/ambiente por geração, catálogo de uso com
  tempos e falhas, prompt IA completo e ZIP de registros com catálogo e snapshots.
- Configuração inválida do worker registrada como falha; progresso/duração
  não finitos tratados. Reutilização temporária de teste NVENC que falhou.
- Limpeza protege caminhos, logs recentes e dados originais. Cópia de vídeo só
  pode ser removida se o SHA-256 do arquivo arquivado coincidir.

## Pacote instalado e rollback

Atualização 1.42.3 → 1.42.4, caminho com acentos/espaços, inicialização fora da
raiz, encerramento controlado, mudança da pasta e rollback para 1.42.3 aprovados.
Arquivos do programa restaurados byte a byte; sentinelas KMZ, GeoTIFF e vídeo
preservadas. Recursos locais e fontes conferidos no pacote instalado.
Tempo de inicialização medido nesse ensaio: 1.807 s;
é uma observação Linux, sem benchmark comparativo ou garantia para outro PC.

SHA-256 do ZIP: `4176ca3a1230e975f3f940542fd0126adf7420101c07a3ed5fa55d173b68d282`.

## DXF TH53 fornecido

Configuração padrão; sem projeto salvo/KMZ e sem confirmação de CRS. Testes
geométricos e simulações de 30 segundos; não certificam todos os conflitos de
cruzamento ou as normas CONTRAN.

| Limite | Segmentos curtos ignorados | Itinerários válidos | Veículos | Colisões traseiras |
|---|---:|---:|---:|---:|
| 50 m | 99 | 4 | 25 | 0 |
| 120 m | 105 | 4 | 25 | 0 |
| 200 m | 108 | 4 | 25 | 0 |

## Prontidão para uso intenso

**6,5/10**, avaliação de engenharia: piloto controlado com backup. A aprovação
funcional não substitui testes nativos Windows/WebView2, nem ensaios prolongados
com vários projetos reais e vídeos longos 4K. Os recursos opcionais DWG/ECW/MrSID
não foram certificados neste Linux. Detalhes em pacote/AUDITORIA_1_42_4.md.
A proposta de evolução CAD/3D está em EVOLUCAO_GRAFICA.md; o editor permanece Canvas.

As regras para futuras revisões foram registradas em rodovia_studio/AGENTS.md.
ZIPs históricos e main preservados. Após instalar, recalcule uma vez os fluxos
do projeto existente com Atualizar fluxos; mudanças posteriores do seletor
solicitam o recálculo automaticamente.
