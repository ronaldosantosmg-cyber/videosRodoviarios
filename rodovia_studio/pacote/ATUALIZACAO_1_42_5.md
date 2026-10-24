# Rodovia Studio 1.42.5

- Remoção de candidatos automáticos menores que o limite antes dos nós e novamente depois dos cortes e da validação da superfície. Não cria entradas de veículos nos cortes rejeitados. DXF e rotas manuais preservados; a circulação manual continua sujeita às regras de segurança.
- Editor antigo exige recálculo após mudar o motor; ao abrir um projeto salvo a interface solicita análise automaticamente quando o cache é incompatível.
- Barra textual duplicada retirada. Ferramentas técnicas imediatamente abaixo dos menus, SVGs Lucide locais licenciados e ajuda por hover/foco. Menus preservam as ações de arquivo e edição.
- Vista WebGL2/Three.js local e opcional, câmera orbital, planta/enquadramento, acompanhamento de veículo, dia/entardecer, inspeção de coordenadas, animação da simulação e retorno ao CAD 2D. Cálculos originais em coordenadas do projeto; buffers gráficos relativos à origem local.
- Prévia 3D de até 60 segundos. Captura PNG e exportação MP4 por quadros de tempo fixo, sem diagnósticos técnicos. FFmpeg local valida todos os quadros antes de publicar; exportação cancelável, sem sequência de imagens temporárias. O vídeo 2D permanece disponível para a duração integral.
- Novo projeto exige identificação, origem/destino e km inicial/final antes de criar; permite escolher configurações técnicas e arquivos iniciais. O título exibe a identificação salva.
- Testes não integram o pacote instalado. Testes antigos só são arquivados se idênticos ao manifesto do ZIP anterior aplicado; versões modificadas/desconhecidas ficam. Rollback restaura os arquivos arquivados. Exemplo TH57 indisponível retirado e arquivado no repositório.

Coloque o ZIP em atualizacoes/ e use a atualização do aplicativo. Preserve os snapshots. Nenhum projeto, vídeo, KMZ ou cache persistente de GeoTIFF é eliminado.

A vista 3D é uma primeira implementação de apresentação e inspeção, sem equivalência funcional ou visual a AutoCAD/Twinmotion. Não certifica CONTRAN, gabaritos de OAE, veículos articulados nem cruzamentos em desnível. Sem MDT confirmado, identifica terreno plano. A simulação 3D usa o motor cinemático validado. Three.js e ícones são locais, sem CDN. Não há IA remota executada automaticamente.
