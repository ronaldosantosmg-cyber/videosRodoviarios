# Rodovia Studio 1.42.33

Revisão dirigida à demora na leitura do DXF e na preparação inicial dos fluxos.

- Normalização de nomes e padrões de camadas reutilizada em cache limitado a 2048 entradas de até 1024 caracteres. Regras manuais continuam sendo consultadas; editar um perfil não conserva uma classificação antiga.
- A análise entrega sua geometria diretamente à preparação dos fluxos na mesma tarefa e configuração, evitando uma segunda leitura/conversão do DXF. Não há cache global de desenhos nem mistura entre projetos.
- Estado de leitura apresentado antes de iniciar a análise; cancelamento conferido novamente antes de publicar os resultados.
- Precisão de curvas, ilhas das hachuras, regras de nós, restrições físicas e atualização completa explícita preservadas.

## Nós: recurso disponível e pendência

Configuração existente: Tráfego → Regras e operação dos fluxos → Eixos, nós e giro das rotatórias. Nó A e Nó B classificam os extremos dos alinhamentos cadastrados; classificação, sentido, giro e demanda externa alimentam o motor compartilhado de cálculo e vídeo.

Ainda não existe um editor gráfico dedicado com comandos Inserir nó, Selecionar nó, Mover nó e Apagar nó no desenho. Não confundir remoção de segmento, recorte ou configuração dos extremos com esses comandos. Esta revisão de desempenho não acrescenta esse editor nem remove conexões existentes.

## Atualização

Coloque o ZIP em atualizacoes/ da instalação e aplique pelo atualizador do aplicativo. Aguarde o encerramento controlado e reabra. Dados persistentes e rollback continuam preservados. A primeira atualização pode invalidar caches derivados por mudança de versão do código.

Ensaio pareado no DXF de referência: preparação de 76.8 s para 20.1 s, com leitura de 2 para 1 e conteúdo geométrico e de fluxos equivalente (exceto revisão do motor e contadores de cache). Carga do host compartilhada; este ensaio isolado não representa todos os computadores.

Consulte evidencias/1.42.33 para testes, medições e limites. O ganho medido no DXF de referência não é uma promessa de tempo em todo projeto ou PC. Compilação/splash com Mono não equivalem à validação nativa Windows.
