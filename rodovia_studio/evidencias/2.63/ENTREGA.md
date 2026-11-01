# Entrega 2.63

Base recebida: 2.60 + 2.61 + 2.62. Código e pacotes exclusivamente na branch de desenvolvimento. Referência main preservada: `4a4e47011ce44f6a33d4fc6f7bc31cac3ec472c3`.

## Resultado

Perfil da revisão: **291 testes aprovados, zero falhas, erros ou ignorados**, relatório consolidado em `pacote/pytest-resultados.xml`. Reaproveitamento por hash idêntico do produto, com repetição dos módulos de testes alterados e dependentes. As tentativas anteriores permanecem para auditoria e não aprovam o produto. Consulte ESCOPO_DA_VALIDACAO.md para limites e a auditoria histórica pendente.

Foram verificados a interface real no Chromium, MP4 2D de 72 quadros / 1280×720 / 24 fps com decodificação integral, WebGL/PNG/MP4, configurações, histórico, seções, sentidos, nós, PER Excel/CSV, cache, sintaxe e compilação C# com/sem WebView2. Splash Mono/Xvfb: versão, fabricante e animação aprovados. Isso não substitui execução no Windows.

## Uso

- Tráfego → Configurar faixas → dividir a seção e editar o segundo trecho; salvar inclui a edição pendente.
- Veículos e fluxo → Exibir veículos somente sobre pavimento cadastrado. O filtro recorta a apresentação da carroceria, mantendo a simulação e as rotas existentes. Confira o cadastro do pavimento se os veículos ficarem ocultos.
- Obras PER → importar Excel/CSV → conferir posição por km no eixo calibrado; as obras fora do trecho ficam sinalizadas, sem serem colocadas numa extremidade.
- Realce de pintura na apresentação; largura métrica da pintura 3D e mapeamentos manuais preservados.

## Limites e prontidão

Nota estimada: **7/10 para uso acompanhado no fluxo testado**. Para uso intenso ainda faltam Windows/WebView2 nativo em 8 GB, carga prolongada, projetos reais representativos e triagem/migração completa das regressões históricas. Não é nota 9, certificação normativa ou garantia universal de ausência de travamentos.

A solicitação posterior sobre cintilação/linhas fantasmas no TH57, perfis Realista/Ultra realista e tons de aterro/corte fica para a revisão seguinte, após disponibilização deste pacote. A referência visual TH57 não está nos anexos atuais: existe apenas ficha técnica sem amostras de imagem.
