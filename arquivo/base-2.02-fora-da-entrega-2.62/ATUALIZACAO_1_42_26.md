# Rodovia Studio 1.42.26 — interface estruturada

Esta revisão reconstrói a estrutura da página, preservando os formulários, identificadores, comandos e APIs do motor existente. Não substitui o motor de cálculo ou o WebGL.

## Alterações

- Documento HTML explícito, sem execução JavaScript embutida no HTML ou atributos onclick.
- Inicialização do tema e estilos de estrutura em arquivos locais separados; módulos originais carregados pelo servidor em ordem.
- Cinco abas, navegação compacta, favoritos, seleção, histórico, painéis e progresso compartilhado preservados.
- Bordas e margens em diálogos, rolagem, ajuste para telas pequenas, foco de teclado, atalho de acesso à área de projeto e redução de animações conforme preferência do sistema.
- Verificação dos recursos nativos do navegador; diagnóstico de instalação incompleta. Ausência do HTML produz HTTP 503 explicativo, sem recriar ou restaurar arquivos automaticamente.
- Identificação do fabricante Ronaldo Santos na interface.

## Instalação e uso

Use a atualização completa pelo atualizador após revisão e liberação da TI. Não substitua somente index.html: a página nova depende também da rota /interface/, dos estilos e dos módulos desta revisão. Preserve projetos/, videos/ e as fontes originais.

Abra o aplicativo pelo iniciador e use a URL local no navegador. Canvas 2D e WebGL usam o próprio navegador; não há plugin gráfico novo. As bibliotecas gráficas existentes continuam locais no pacote. O servidor/motor existente continua necessário para arquivos, cálculos, simulação e MP4. Esta entrega não é uma aplicação HTML autônoma para abrir com duplo clique.

## Segurança e limites

A reconstrução não comprova falso positivo nem elimina por si o alerta Trojan:Script/Ulthar.A!ml. O núcleo JavaScript preexistente permanece utilizado; não alteramos nomes ou código para contornar detecção. Não restaurar quarentena, desativar proteção ou adicionar exclusões. Solicitar análise do pacote pela TI/Defender antes da execução.

Testes desta revisão e seus limites constam de evidencias/1.42.26. Chromium foi o navegador disponível para validação. O download do Firefox para teste foi bloqueado pela política de rede (HTTP 403); Firefox e Edge nativos não estão certificados por estes ensaios. O teste 3D usa renderização de software no ambiente de teste, não mede desempenho da GPU do usuário. Não há alegação de ganho mensurado de FPS/memória ou de qualidade máxima.
