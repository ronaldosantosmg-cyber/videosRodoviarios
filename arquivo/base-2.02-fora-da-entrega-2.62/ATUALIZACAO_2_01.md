# Rodovia Studio 2.01

Revisão integrada sobre a 1.42.38, com schema 31 preservado. O número 2.01 foi solicitado pelo usuário; não representa substituição do motor nem homologação Windows.

## Operação

- Abrir painéis ou redimensionar a janela preserva centro e escala do desenho em pixels CSS; mudança de DPI adapta apenas a resolução física.
- Capturas de imagem preservam a vista anterior quando a referência de coordenadas permite.
- Aplicar no painel principal salva sem fechar. Descartar posteriormente retorna à última aplicação confirmada, preservando dados já salvos.
- Formulários de modelagem conferem campos antes de executar a gravação; falhas mantêm o rascunho e liberam os controles.
- Salvar e atualizar nos formulários usa a fila compartilhada, sem a segunda espera arbitrária de dois minutos.
- Camadas e catálogo de materiais são ordenados alfabeticamente, com comparação numérica; ordem técnica de eixos e seções não foi alterada.
- Contraste de botões, foco de teclado e ícones principais foram ajustados.
- Materiais naturais podem ser apresentados nos vetores 2D, respeitando mapeamentos por camada. Use Cena → Materiais e texturas → Usar materiais naturais. É uma amostra local do catálogo, não identidade visual ou resolução equivalente ao render final.
- Mudança de aparência invalida a camada técnica, sem invalidar a imagem aérea ou iniciar uma simulação somente para redesenhar a tela.
- A orientação de corpo fora da pista distingue seção operacional, apresentação fora do pavimento e impedimentos reais.

## Compatibilidade e preservação

O motor existente de seções, nós, sentidos, arrasto, semáforos, barreiras, interdições e OAE é reutilizado. Nenhuma regra de segurança foi desligada para remover alertas. A revisão não substitui o cadastro de veículos por dimensões supostamente normativas.

Contornos decorativos e OAE com Z zero já possuem regras específicas; sua existência não comprova que qualquer classificação manual esteja correta. Use a central de diagnóstico e confira o eixo e a seção cadastrados.

Não foram excluídos módulos por ausência de referências estáticas. As extensões e rotas são dinâmicas. Foi retirada a espera paralela obsoleta dos formulários; o restante foi preservado até comprovação de desuso.

## Atualizar

Salve o projeto e mantenha cópia. Coloque o novo ZIP em atualizacoes/ e use o atualizador do próprio aplicativo. Não extraia sobre o programa aberto. Preservar projetos/, videos/, fontes CAD/KMZ, imagens originais e cache persistente GeoTIFF. Snapshot, encerramento controlado e rollback continuam necessários.

## Limites

Testes da revisão devem acompanhar a entrega. Não declarar ausência universal de erros, conformidade DNIT/CONTRAN, desempenho em 8 GB ou validação Windows nativa sem execução específica. Modelo de IA 3B não está incluído.
