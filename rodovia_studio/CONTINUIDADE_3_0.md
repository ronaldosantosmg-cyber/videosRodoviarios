# Continuidade do Rodovia Studio 3.0

Repositório: https://github.com/ronaldosantosmg-cyber/videosRodoviarios

Branch de trabalho: `desenvolvimento/rodovia-studio-3.0`. Não usar a main como fonte desta revisão. Não fazer merge na main sem autorização explícita do usuário.

## Obter o código

```bash
git clone --branch desenvolvimento/rodovia-studio-3.0 --single-branch https://github.com/ronaldosantosmg-cyber/videosRodoviarios.git
cd videosRodoviarios
```

Leia `rodovia_studio/AGENTS.md`. A aplicação mantida fica em `rodovia_studio/pacote/suporte/sistema/`. O CLI `src/` é outro componente; não substituir o aplicativo por ele.

O ZIP completo fica em `atualizacoes/RodoviaStudio_3_0_atualizacao.zip`. A base consolidada é a 2.69, com suas alterações de TRIM, contornos DXF, classificação e ícones, mais a apresentação da 3.0. Não foi publicada revisão 2.70: esse número aparece nos nomes históricos dos testes/artefatos da implementação, que foi renumerada 3.0 a pedido do usuário. A versão de entrega é definida por `pacote/manifest.json` e `pacote/suporte/sistema/VERSAO.json`.

## Alterações desta entrega

- `existing_visibility`: existentes visíveis desde o início ou revelados com o avanço; campo de apresentação persistente, com teste de salvar/descartar.
- Pavimento projetado prioritário sobre o existente na composição do mosaico, detalhe e editor; paleta de asfalto novo escura e mais uniforme, existente mais clara/neutra e desgastada. Cores e materiais manuais preservados.
- `presentation.py`: classificação visual existente/projetado, subcamada existente, máscara longitudinal comum e composição. Não usar essa classificação para liberar uma rota ou alterar sua segurança.
- `render.py`/`detail.py`: duas fases visuais, máscaras/snapshots/cache, correção das linhas de OAE existente que recobriam pavimento novo, água do CAD progressiva e sinalização/feições dinâmicas acompanhando a frente. Congelamento protege apenas edição.
- `scene3d.py` e `webgl/reveal.mjs`: afastamento visual de superfícies coincidentes; campo visual longitudinal limitado para revelação durante captura. A vista de edição continua completa e é restaurada ao terminar. Captura 3D mantém veículos, sinais, trens e demais dados físicos do motor existente.
- Vídeos curtos usam revelação espacial; o último quadro conclui a frente. DXF pode anteceder a textura pelo avanço configurado.
- Rede, sentidos, nós, seções, demanda, colisões, interdições e semáforos continuam no motor existente. Não criar um segundo motor de tráfego.

## Evidências e limitações

Consulte `evidencias/3.0/entrega_final/resultado.json`, relatório XML, imagens e logs da validação final. `pacotes-verificados.json` registra aplicação, rollback e preservação dos dados dos ZIPs exatos. `publicacao.json` registra downloads HTTPS e SHA-256. Tentativas em `evidencias/2.70/` pertencem ao desenvolvimento, não aprovam a entrega 3.0.

O teste de transporte foi ajustado às cinco abas atuais e à proteção de clique durante a estabilização após redimensionamento. Não remover a proteção para fazer um teste passar. Os nomes de testes `v270` identificam a tarefa histórica, não uma versão separada a instalar.

Ambiente de teste Linux/Chromium/SwiftShader, Python e Mono/Xvfb; sem homologação Windows nativa/Defender ou certificado de assinatura. O DXF/configuração exatos do TH57 não foram localizados nesta sessão. Não afirmar validação integral do TH57, conformidade normativa ou ganho de desempenho no PC de 8 GB sem reproduzir e medir.

## Como continuar

1. Conferir a versão efetiva e o commit antes de alterar.
2. Reproduzir a solicitação com projeto salvo/configuração, mantendo fontes DXF/KMZ/imagens originais.
3. Fazer mudanças pequenas no mesmo motor e nos componentes existentes.
4. Executar testes dirigidos proporcionais; usar `validar_entrega.py` e respeitar os resultados, sem ocultar falhas ou ignorados. Python/Node/Chromium/FFmpeg e compilador C#/WebView2 SDK são necessários para o gate completo. Variáveis de dados/cache devem apontar para pastas temporárias durante os testes.
5. Somente após aprovação gerar nova revisão, com ZIPs exclusivamente em `atualizacoes/` na raiz; preservar históricos. Verificar aplicação, rollback, SHA-256 e download HTTPS.
6. Preservar projetos, vídeos, fontes, cache GeoTIFF persistente, histórico, seleção e enquadramento. Não limpar pastas genericamente nem remover código apenas por busca estática.
