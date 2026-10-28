# Rodovia Studio 1.42.37

Correções de fluxo, imagem combinada, UTF-8 e organização da interface.

## Atualizar

1. Salve o trabalho e mantenha uma cópia do projeto. Coloque o ZIP em atualizacoes/ e selecione-o na atualização do próprio Rodovia Studio.
2. Confirme o encerramento controlado. O atualizador confere o manifesto e cria o snapshot antes da troca. Reabra pelo iniciador.
3. Projetos/, videos/, DXF/KMZ, imagens originais e cache persistente não são conteúdo descartável da atualização. Não extraia o pacote sobre o aplicativo aberto.
4. Para voltar da 1.42.37 à 1.42.36, use o rollback da instalação. Projetos usam o mesmo schema 31. Para revisões anteriores à 1.42.36, preserve a cópia anterior do projeto: vínculos novos de sentido não são entendidos por revisões antigas.

## Conferir veículos

Em Tráfego → Diagnosticar veículos, confira pavimentos/hachuras, sentidos/nós e o modo de operação. Novos padrões reconhecem HATCH_PAV_NOVO, HATCH (pista) e variantes de pavimento existente. Mapeamentos manuais não são substituídos automaticamente: revise e aplique somente as camadas corretas. Depois, atualize e confira a prévia de tráfego.

A prévia sem alvo permite abrir a vista geral para corrigir. Exportar com veículos ativados e sem itinerário é recusado com orientação, preservando o vídeo anterior. ENSAIO fica nos avisos/metadados, sem mensagem nos quadros. Em imagem combinada, falha de rede pode usar imagem local válida e fundo neutro fora da cobertura, com aviso.

## Limites

Evidências e resultados da validação acompanham o pacote. Sem homologação nativa Windows/8 GB, conformidade normativa ou garantia universal de reconstrução de ligações. Trechos recusados continuam exigindo conferência. Não inclui pesos de IA 3B. Prontidão para uso intenso estimada em 7,8/10: homologação em projeto real e operação prolongada ainda são necessárias.
