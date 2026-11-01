# Rodovia Studio 1.42.38

Correção do acompanhamento e da espera de tarefas. A geometria, os critérios de fluxo e os cálculos não foram substituídos.

## Atualizar

Salve o projeto e mantenha cópia. Coloque este novo ZIP em atualizacoes/ da instalação e use o atualizador do Rodovia Studio. Confirme o encerramento controlado e reabra pelo iniciador. Não extraia sobre o programa aberto. Projetos, vídeos, fontes DXF/KMZ, imagens originais e cache persistente GeoTIFF devem ser preservados. Rollback para 1.42.37 disponível pelo atualizador; schema 31 mantido.

## O que muda

- A consulta de andamento tenta reconectar à mesma tarefa, sem reenviar o cálculo.
- Retomar fica visível no rodapé compacto e antecipa a próxima consulta. O cálculo não é reiniciado.
- A fila não falha por esperar mais de dois minutos; aguarda também a aplicação dos resultados recuperados. Pedidos equivalentes continuam compartilhados.
- Limpar fila descarta pedidos pendentes, sem cancelar a tarefa atual. Cancelar solicita o cancelamento da tarefa no servidor.
- Duas consultas redundantes após a conclusão foram retiradas; os componentes reutilizam a resposta final.
- Falhas reais de cálculo continuam sendo informadas. Erros de acesso não autorizam reenviar o cálculo automaticamente.

Enquanto a conexão estiver indisponível, o estado real do cálculo permanece incerto. Não interprete ausência de resposta como prova de travamento. Esta correção não identifica por si só a causa inicial de uma interrupção de rede/servidor.

## Validação e limites

Relatórios funcionais e visuais acompanham o pacote. Prontidão de referência: 7,8/10; sem homologação nativa Windows/WebView2 em 8 GB, carga prolongada ou garantia universal de ausência de travamentos. Não inclui pesos de IA 3B. Esta revisão é restrita ao acompanhamento/fila, sem alteração dos critérios de segurança dos fluxos.
