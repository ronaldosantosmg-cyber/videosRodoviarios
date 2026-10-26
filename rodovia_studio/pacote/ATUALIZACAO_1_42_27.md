# Rodovia Studio 1.42.27

## O que mudou

- Corrigido o contrato `RodoviaDesktopWorkspace`: Modo Projeto e Linha de comando usam as funções existentes, com retorno por F11/Ctrl+Espaço.
- Pontos amarelos pulsantes e clicáveis sobre os problemas do editor 2D. O diagnóstico mostra causa, passos, Localizar, Analisar correção com IA e Editar trecho. A assistência de execução prioriza o trecho indicado.
- Marcadores ficam numa camada DOM do estudo, fora do bitmap Canvas e do renderizador de vídeo. Não são gravados no projeto, no MP4 ou na captura do Canvas. A animação usa CSS, não recalcula o motor nem regenera o desenho. Máximo de 200 marcadores visíveis; coordenadas inválidas são rejeitadas. A preferência de movimento reduzido mantém os pontos estáticos.
- Se não há ponto exato, uma referência no meio do trecho é identificada como referência, sem afirmar precisão inexistente. Diagnóstico anterior avisa sobre atualização pendente. Fluxos válidos, desligados manualmente ou excluídos pelo limite de comprimento não recebem marcador; a assistência informa as exclusões intencionais separadamente.
- Mais painéis organizados em Projeto e configuração, Cena e apresentação, Manutenção e assistência. Cascatas usam o menu existente, teclado, limites da janela, segundo clique para retrair e Escape para retornar o foco.
- Configuração de vídeo em cinco grupos: Exportação, Câmera, Veículos e fluxo, Aparência, Avançado. Campos e eventos originais são movidos, sem cópias ou configurações paralelas. Preservados Salvar, Descartar, densidade e comunicação com o motor.
- Regras locais adicionais para erros de interface, integridade, revisão obsoleta, impedimentos físicos, seção, materiais, WebGL e espaço em disco. Logs oferecem atalhos revisáveis para as ferramentas originais. Nenhum texto de log ou resposta externa é executado como código.

## Uso

Atualize com o pacote completo pelo atualizador. Abra Tráfego e gere/atualize o diagnóstico. Clique numa bola amarela no editor para localizar o defeito e ler a orientação. Analisar correção com IA abre a proposta pelo motor; confirme somente após conferir e revalide o resultado. Desfazer continua disponível. Uma sugestão não libera uma rota por si.

Em Vídeo → Configurar vídeo, use as abas internas. Salvar e fechar confirma os mesmos campos usados pelo cálculo e pelo vídeo. Fechar com alterações permite salvar, descartar ou continuar editando.

## Limites e preservação

Não é uma reconstrução universal de qualquer malha nem IA generativa incorporada. Não remove barreiras reais, colisões, sentidos, interdições ou semáforos para eliminar avisos. Os pontos novos são do editor 2D; o diagnóstico gráfico 3D existente permanece separado. Não há alegação de homologação normativa ou desempenho universal.

Preservados projetos/, videos/, fontes DXF/KMZ, imagens originais, cache persistente GeoTIFF, perfis, snapshots, fechamento controlado e rollback. Não há limpeza genérica destrutiva. Main não foi alterada.

Evidências atuais e limites de plataforma estão em rodovia_studio/evidencias/1.42.27 no repositório.
