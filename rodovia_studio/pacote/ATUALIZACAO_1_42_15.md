# Rodovia Studio 1.42.15

Correção prioritária: atualizar ou recalcular rotas preserva o centro da vista em coordenadas do projeto e a escala. Uma prévia tornada desatualizada não é mais descartada da tela do projeto já aberto; permanece como referência, marcada desatualizada. Isso não aprova sua exportação nem substitui a necessidade de recalcular resultados técnicos. Falhas temporárias na imagem preservam a imagem anterior. Corrigida a exceção na lista de camadas quando há fluxos, mas ainda não há vetores georreferenciados.

Faixa técnica horizontal com transbordamento e grupos por função, controles de imagem reunidos à faixa e barra lateral recolhível. Os controles existentes mantêm seus eventos e identificadores. Área gráfica medida em Chromium Linux: de 479 para 579 px de altura em janelas 1024×900 e 1366×900; de 528 para 579 px em 1920×900.

Fundo e vetores georreferenciados reutilizam dois caches auxiliares 2D, compondo com o canvas de interação existente. Limite adicional de 32 MiB; acima dele, ou sem contexto auxiliar, utiliza desenho direto. Invalidação por câmera, dados, configuração e carregamento de ladrilhos. Coordenadas, cálculos, dados originais e motor WebGL permanecem compartilhados. Marcações editáveis e elementos dinâmicos continuam no canvas de interação. O resultado de velocidade medido é sintético e não significa aumento equivalente de FPS em todo projeto.

Validação direcionada autorizada pelo usuário, com testes de interface, fluxo, estado, falhas de carregamento, memória de cache e regressão em DXF real. A suíte integral e o Windows/WebView2 nativo não foram executados nesta revisão. A instalação e o rollback são conferidos em diretório independente com preservação de projetos, vídeos e cache.

Pendências explícitas: fumaça ferroviária e novo motor de pedestres com segurança entre agentes, veículos e trens não integram esta entrega. O protótipo está preservado fora do pacote, aguardando integração e testes 2D/3D/vídeo.
