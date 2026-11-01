# Rodovia Studio 2.66 — entrega

Continua os fluxos operantes da base recebida 2.62 e inclui as correções 2.63: apresentação do veículo limitada ao pavimento cadastrado, duas seções por eixo com edição pendente salva, pintura métrica 3D e localização PER Excel/CSV no eixo calibrado.

A numeração **2.66** foi solicitada pelo usuário para distingui-la de uma 2.65 produzida em outra origem. Esta entrega continua a base 2.63 desta sessão e seus complementos visuais. Não declara incorporação da 2.65 externa, que não foi fornecida/comparada. Os ZIPs locais de rascunho 2.65 ficam em `atualizacoes/rascunhos-nao-distribuidos/`, fora da busca automática.

## Mudanças desta revisão

- Frente DXF de 30 m (ajustável de 0 a 150 m), antes dos materiais na animação progressiva. Usa arestas reais do projeto, não liga entidades separadas e não permanece sobre a apresentação concluída.
- As linhas amarelas de domínio ficam no modo técnico; sua exibição artística é opcional. Fechamentos virtuais sinalizados pelo leitor de hachuras abertas não são tratados como contorno real. O desenho e os cálculos não são apagados.
- Correção do estaqueamento de pixels do desenho de detalhe ausentes no mosaico grosseiro: partes legítimas do DXF deixam de ser ocultadas indevidamente durante a construção progressiva.
- Perfis Ultra realista (identifica o detalhe existente) e Realista (menor microdetalhe). As escalas de ruído são físicas e o nível de detalhe muda continuamente com a resolução.
- Aterros/terreno verdes, cortes avermelhados; cores manuais preservadas em 2D/3D. O relevo de taludes não é mais descartado no mosaico principal. A composição tem a mesma referência no mosaico e nos ladrilhos de detalhe.
- Os campos de avanço DXF e contorno técnico não invalidam a geometria, a simulação ou a cena 3D estática. O perfil de detalhe invalida a aparência correspondente.
- GATE por risco: perfil curto com comportamentos verificáveis; mudanças fora do escopo conhecido elevam o perfil. Prazo de 180 s para os testes curtos, com encerramento dos filhos e bloqueio do ZIP se houver falha/tempo excedido. Perfil amplo permanece disponível.

Os arquivos `traffic.py`, `simulation.py` e `routes.py` permanecem idênticos aos da 2.63. Não foram alteradas as regras dos nós, sentidos ou conservação do tráfego.

## Evidências

- `entrega/resultado.json`: **85 testes, zero falhas, erros ou ignorados**. Os tempos da execução 2.66 constam em `entrega/resultado.json` e no XML. Não é benchmark do aplicativo em um PC Windows.
- `entrega/266_videos.json`: MP4 de ambos os perfis, H.264 / 1280×720 / 24 fps / 72 quadros, com decodificação conferida.
- Capturas novas: perfis, janela salvar/descartar, WebGL, com/sem contornos, frente DXF e obra concluída.
- `estabilidade-controlada.json`: em patch sintético a ~0,2 m/pixel, variação de zoom de 0,0001 m/pixel mudou a diferença média de 13,981 para 0,429 níveis RGB. É uma comparação controlada do shader, não redução medida na nova renderização exata do TH57.
- `gravacao-metadata.json` / `gravacao-analise-temporal.json`: gravação recebida, 203 quadros, 30 fps, 1664×832, 6,77 s; 67 pares alinhados aproximadamente. Compressão, veículos e parallax também afetam a medida.
- DXF preservado: `DUPLICAÇÃO TH53.dxf`, 21.106.984 bytes, 15.128 entidades, 295 camadas. As quatro entidades de domínio analisadas não possuíam fechamento virtual sinalizado; seus contornos reais foram preservados. Não se inventa um diagnóstico de corrupção. A exibição de domínio na maquete é uma opção de apresentação.
- `pacotes-verificados.json`: aplicação e rollback dos ZIPs exatos com preservação de projeto, KMZ, GeoTIFF persistente e vídeo; pacote leve recusado em base anterior à exigida.

O MP4 original recebido e o DXF do usuário ficam fora dos pacotes e não foram publicados no repositório.

## Usar

Cena → Materiais e texturas: escolha Realista ou Ultra realista, ajuste Avanço do DXF antes da textura (30 m inicial) e confirme. Use 0 para uma apresentação sem a frente de contorno. Contornos técnicos na apresentação artística fica desmarcado por padrão. Para inspecionar todas as referências, use o modo Técnico.

Feche o aplicativo, coloque um único ZIP em `atualizacoes/` da instalação e use o atualizador. O completo já inclui todas as revisões anteriores; não é necessário instalar 2.64. O leve exige 2.63 ou posterior. Preserve os ZIPs históricos.

## Limites e prontidão

**7/10 para uso acompanhado** no fluxo testado. Permanecem pendentes Windows/WebView2 nativo, carga prolongada em 8 GB, auditoria integral do legado e uma reprodução completa do TH57 com a configuração e imagens locais exatas. A gravação foi inspecionada e a causa de instabilidade do shader foi reproduzida em teste controlado; não se afirma que qualquer linha ruim de qualquer DXF tenha sido corrigida automaticamente ou que a qualidade equivalha ao Twinmotion.

Main preservada: `4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3`.
