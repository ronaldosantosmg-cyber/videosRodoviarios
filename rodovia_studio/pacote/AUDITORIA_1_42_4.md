# Auditoria para uso intenso — revisão 1.42.4

## Avaliação de prontidão

**Nota técnica: 6,5/10 para uso intenso em produção no Windows.** É um julgamento
de engenharia, não um índice calculado por quantidade de testes. O conjunto
atual permite um piloto controlado com cópias de segurança. A nota considera
as proteções e verificações funcionais, mas não certifica operação contínua.

O que ainda impede classificar como pronto para uso intenso: execução nativa
Windows/WebView2 e PowerShell não validada neste Linux; falta ensaio prolongado
com vários projetos reais, vídeos longos em 4K, memória, drivers gráficos e
interrupções de energia/disco cheio; não há certificação de conformidade viária.
O limite de comprimento não prova que o restante da rede esteja livre de todos
os conflitos. Os sentidos e restrições do projeto precisam ser conferidos.

## Recursos locais e funções opcionais

Os componentes Python do núcleo e o FFmpeg são verificados localmente por
`/api/capacidades`. DXF, KMZ, GeoTIFF, edição, simulação, vídeo e geração do
prompt IA usam recursos locais. As fontes DejaVuSans regular/negrito estavam
faltando no pacote; agora são incluídas com licença, eliminando a dependência
acidental de fontes disponíveis no sistema de teste.

DWG depende do ODA File Converter. ECW/MrSID dependem de drivers/componentes
opcionais, que não podem ser considerados instalados apenas por existir uma
função no código. No ambiente Linux de validação, esses recursos opcionais não
foram certificados com arquivos reais. Eles continuam disponíveis quando seus
componentes estão presentes; DXF e GeoTIFF são alternativas locais. Consultas
online de imagem, cidades e hidrografia exigem rede ou cache. Nada envia os logs
para uma IA automaticamente: o prompt é gerado localmente para revisão do usuário.

## Proteções compartilhadas

Validação de configurações, finitude, geometria e trajetórias permanece no
código comum, utilizada por qualquer projeto. A nova revisão acrescenta:
tratamento de duração/progresso inválidos; erro de configuração do worker
registrado como falha sem deixar a tarefa em execução; zoom com eventos finitos,
normalização de unidades e escala limitada; desfazer/refazer com invalidação de
caches e histórico limitado em memória; limpeza sem seguir links para outras
pastas e retenção de registros recentes.

Versões futuras devem conservar essas verificações na validação de entrega.
ZIPs históricos permanecem imutáveis para referência e rollback; uma instalação
antiga só recebe as novas proteções ao aplicar a atualização.

## Código legado e funções sem uso

Foi retirado o controle antigo Mostrar nomes da interface oculta; a nova barra
usa ajuda ao passar o mouse e no foco do teclado. Textos de ajuda que apenas
remetiam a versões antigas foram substituídos por descrições da função.

A busca por definições Python repetidas no mesmo módulo não encontrou funções
sobrescritas dessa forma. Isso não prova ausência de funções órfãs: registro de
rotas, extensões JavaScript e carregamento de workers são dinâmicos. Não foi
identificada outra função cuja remoção fosse comprovadamente segura nesta
revisão. Não foram desativadas funções por simples busca de nomes.

Migrações, aliases de comando, modos de compatibilidade, testes históricos e
menções a versão anterior no rollback têm finalidade. Foram preservados, assim
como o aplicativo antigo separado em src/, que não compõe este pacote.

## Desempenho, limpeza e reprodução

A escolha do encoder continua fazendo um teste real. Uma falha do teste NVENC é
reutilizada por até 60 segundos, por executável/configuração, evitando repetir
uma tentativa potencialmente lenta. Uma alteração do executável invalida a
chave; depois do prazo, a disponibilidade é testada novamente. Resultado positivo
não é armazenado. Não houve redução de resolução, qualidade ou verificação MP4.

O log registra duração monotônica das etapas e espera até iniciar o worker.
O servidor registra tempo até concluir a inicialização. O catálogo de uso agrega
amostras, média, p95, máximo, falhas e sugestões com evidência. Ele não estabelece
causalidade sozinho nem representa eventos que já tenham sido apagados.

O prompt inclui configuração completa, configuração capturada no início da
geração, hashes de entradas, versões do ambiente e FFmpeg, logs e catálogo. O
ZIP de registros inclui os snapshots. Alterar arquivos/cache/encoder/máquina pode
mudar o resultado; não é prometida identidade binária do MP4. Dados e logs são
tratados como evidência, sem execução automática de instruções de uma IA.

A limpeza preserva logs dos últimos 30 dias, projetos, dados originais e cache
persistente de GeoTIFF por padrão. A cópia de trabalho de um vídeo só é removida
na categoria opcional correspondente se o vídeo arquivado existir na pasta
permitida e seu SHA-256 coincidir — mesmo tamanho já não basta.

Próximas otimizações devem partir das etapas medidas: preparação de geometria,
cache, rasterização, cópia de quadros, número de processos e encoder. Validar a
qualidade e medir novamente com a mesma cena antes de mudar parâmetros.
