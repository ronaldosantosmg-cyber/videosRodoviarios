# Entrega 1.42.10

## Comportamento implementado

- Barra técnica abaixo dos menus: apagar intervalo por início/fim, juntar dois subsegmentos na ordem do fluxo, ajuda por hover/foco e Desfazer. O corte exclui circulação sem apagar o DXF. A junção usa coordenadas completas e rejeita sentido, nível, pista e conexões incompatíveis.
- Recuperação de fluxo principal no motor comum a qualquer projeto: suavização derivada de até 0,5 m somente após revalidação; caso insuficiente, exclusão localizada e revalidação de cada parte. Respeita limites mínimos e desativações manuais. Não cria travessia de lacunas. Setas de sentido e pontos conflituosos são técnicos e não saem no vídeo.
- Ferrovia por seleção de trajetória em tela, seguida da escolha do modelo, sentido, linha simples/dupla e composição de 5–100 vagões. Faróis noturnos, braços projetados e lentes semafóricas ativas em planta/3D. OAE e níveis explícitos são considerados na retenção ferroviária; informações ambíguas não liberam cruzamento.
- Catálogo local de 32 materiais procedurais e perfis reutilizáveis de nomes CAD: OAE, árvores, hidrologia, ferrovia, gás/Gasmig, rede elétrica, postes, edificações, fibra óptica, radar, torre, erosão, cortina atirantada, gabião e offset/off set. Classificações explícitas existentes são preservadas. Cadastro de novos aliases em janela com salvar/descartar/continuar.
- Proteção contra resultados de revisões antigas, cancelamento de operações assíncronas e concorrência entre recálculo automático e manual. Conservação de projetos, originais e cache persistente; campos novos opcionais para leitura pela revisão anterior em rollback.

## Uso

Em **Fluxos de tráfego**, passe o mouse pelos ícones para localizar **Apagar intervalo do fluxo** e **Juntar subsegmentos**. Para recuperação automática, selecione uma trajetória e abra as propriedades, ação **Recuperar fluxo principal…**. Em **Ferrovia e semáforos**, use a seleção de rota na tela e configure o material rodante. Em **Áreas e sinalização**, abra **Materiais, símbolos e nomes CAD** e use **Reconhecer nomes do DXF** ou cadastre um perfil.

## Limites e prontidão

Nota técnica provisória para uso intenso: **7/10**. Há evidência automatizada de motor, API, edição, imagens, camadas, popups, WebGL, vídeo e atualização/rollback; ainda falta validação nativa no Windows/OneDrive/WebView2, nos conversores DWG/ECW efetivamente instalados pelo usuário, em projetos reais salvos e em sessões prolongadas. A nota não é uma medição de satisfação de campo nem certificação normativa.

Texturas e dimensões não levantadas são ilustrativas e identificadas. Não certificam profundidade de rede, gabarito, volume de terraplenagem, luminotecnia ou conformidade CONTRAN. Recuperação parcial não promete continuidade integral. O ensaio agregado do EIXO_LESTE está em ensaio_eixo_leste.json; ele usa o DXF disponibilizado e uma superfície de auditoria, sem reproduzir a configuração salva do usuário e sem alterar o arquivo original.

## Validação final

405 testes aprovados; zero falhas, erros ou ignorados. Sintaxe Python/JavaScript e dependências verificadas; iniciador C# compilado com e sem WebView2; splash com versão, fabricante e animação validado em Mono/Xvfb. Os avisos de depreciação Starlette/httpx e de compilação CS0162 não impediram os testes. Execução completa em Linux: 802,59 s.

O ZIP foi aplicado sobre a 1.42.9 em diretório com espaços e acentos, executado fora da pasta raiz e encerrado pela API de controle. Após mover a instalação, o rollback restaurou todos os arquivos anteriores byte a byte. Sentinelas KMZ, GeoTIFF e vídeo foram preservadas. Zero resíduos do programa arquivados nesse ensaio; dados pessoais não integram o pacote. Compilação/Mono não equivalem a execução nativa Windows.

- ZIP: `RodoviaStudio_1_42_10_atualizacao.zip`; 11,697,620 bytes.
- SHA-256: `e72c42a295320d370853e922c3a82dc53ec1b450afbcf8dcf73b2834f866ad8e`.
- Fonte validada: `6ecabe638dfb42d3944fbb65fdeeb5311836a60929e6b2d9857151f4d84580f8`.
