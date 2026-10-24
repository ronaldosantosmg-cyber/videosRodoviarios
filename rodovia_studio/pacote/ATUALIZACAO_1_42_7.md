# Rodovia Studio 1.42.7 — estado e sincronização

Primeira implementação das etapas 3 e 4 do plano, na branch de desenvolvimento. Não altera a main.

## Gravação e recuperação

A configuração passa pelo mesmo serviço de persistência, com trava entre processos, troca atômica, revisão SHA-256 e histórico limitado de configurações (20 revisões / 64 MB, conservando a atual e a anterior). O cliente envia a revisão que abriu: outra janela que já gravou provoca conflito, preservando a edição local e Desfazer. Não sobrescreve silenciosamente a gravação concorrente. Clientes antigos sem If-Match continuam compatíveis, sem essa garantia de concorrência otimista.

As gravações da interface são serializadas. Digitar durante uma gravação mantém a indicação de alterações pendentes; respostas de uma janela ou projeto anterior não confirmam o projeto atual. Abrir outro projeto aguarda salvar as alterações pendentes; um conflito impede essa troca.

Arquivo → Histórico e recuperação permite selecionar uma configuração gravada. A configuração substituída continua no histórico. Não restaura uma versão anterior de DXF/KMZ nem de vídeos. Configuração corrompida é copiada para `.estado/corrompidos/` e recuperada da última configuração válida registrada. Sem cópia válida, apresenta erro em vez de inventar um projeto vazio.

A substituição dos arquivos principais DXF/DWG/KMZ publica entrada, confirmação de coordenadas e metadados em uma transação com diário. Uma interrupção antes da confirmação reverte o conjunto na próxima leitura. As cópias dos arquivos dessa transação ficam em `.estado/importacoes/`, sem apagar fontes originais, GeoTIFF persistente ou vídeos. A transação não abrange ainda todos os tipos de upload auxiliares, como mosaicos de imagens.

## Sincronização dos resultados

Geometria, tráfego, apresentação, prévia, vídeo e cena 3D possuem revisões de dependências comuns. Trocar textura ou parâmetros da câmera não invalida a geometria dos trajetos. Alterar tráfego invalida seus resultados, sem mudar a revisão da geometria-base. Uma análise já válida é reaproveitada sem recalcular os trajetos.

Cada tarefa principal registra a revisão de origem e os arquivos produzidos. Um processamento que termina depois de uma edição não passa a ser anunciado como atual. Editor, vetores, imagem de prévia e cena 3D recusam resultados registrados como desatualizados, incompletos ou em processamento. Arquivos antigos sem registro permanecem identificados como não verificados quando não possuem revisão própria. Vídeos históricos continuam disponíveis; não se afirma que foram renderizados pela configuração atual.

A conclusão de uma tarefa recarrega somente resultados, preservando marcações, rascunhos, seleção, vista e Desfazer. Terminar uma tarefa de outro projeto não muda o projeto aberto. Fluxos ausentes/desatualizados são recalculados com uma tentativa por revisão; não inicia geração de vídeo automaticamente. O WebGL acompanha a revisão da cena, pausando quando desatualizado.

## Validação e limites

`validar_entrega.py --gerar` é obrigatório antes do ZIP: regressões funcionais e visuais, navegador real, exportação e decodificação de vídeo, JavaScript, Python, compilação C# com/sem WebView2 e splash. Os novos testes cobrem dois processos concorrentes, gravação interrompida, importação interrompida, resposta atrasada, edição durante salvamento, troca de projeto e recuperação pela interface.

É uma migração incremental: extensões antigas da interface continuam operando através do coordenador. Não equivale à conclusão de toda a refatoração nem à validação de uso intenso. Ainda faltam ensaio nativo Windows/WebView2/GPU, sessões prolongadas, projetos grandes representativos e medição comparativa de tempo/memória/4K. Os controles de tráfego permanecem modelos de estudo, sem certificação normativa.

Instale pelo atualizador do aplicativo. O ZIP deve ficar somente em `atualizacoes/`; a instalação mantém snapshot e rollback. Não extrair sobre projetos ou vídeos.
