# Rodovia Studio 1.42.21

Continuação da 1.42.20 na branch de desenvolvimento. Esta revisão simplifica a operação e reaproveita os motores existentes.

## Atualizar e usar

1. Guarde o ZIP em `atualizacoes/` da instalação e use **Arquivo → Atualizar o Rodovia Studio**. Aguarde o encerramento controlado e reabra o programa. Projetos, vídeos, imagens originais e cache GeoTIFF permanecem preservados.
2. Use **Projeto** para arquivos/camadas/imagens, **Editar** para desenho, **Tráfego** para eixo/seção/correção, **Cena** para materiais e 3D e **Vídeo** para prévia/exportação. Ferramentas adicionais ficam em **Mais ferramentas**.
3. Salve normalmente. **Salvar não inicia cálculos.** Quando aparecer **Atualização pendente**, clique **Atualizar** ou **Gerar e visualizar**. A última vista continua disponível enquanto o resultado novo é preparado.
4. Em Tráfego: **Escolher eixo → Configurar faixas → Gerar e visualizar**. Para um impedimento real, use **Corrigir problemas**, localize a causa e tente a correção apropriada. Não há liberação indiscriminada de rotas.
5. Em Cena, abra **Materiais e texturas**, escolha Técnico, Maquete artística ou Personalizado. Materiais locais continuam procedurais. Confira a prévia antes do vídeo final.

## Alterações

- Oito menus e cinco abas, sem “Todas”. Apenas a aba ativa mostra ferramentas. Navegação/histórico e Atualizar permanecem acessíveis; ajuda por hover/foco.
- Progresso único no rodapé para tarefas, captura 3D e downloads, com cancelamento, tempo decorrido e percentual quando disponível. Sem estimativa restante inventada.
- Removidos os disparos automáticos de análise/prévia ao salvar, alterar sentido e concluir formulários. Valores confirmados continuam sendo persistidos no motor.
- Fila limitada, pedidos equivalentes compartilhados e descarte de contexto antigo. Há **Limpar fila** para solicitações ainda aguardando execução.
- Dependências separadas entre geometria, topologia, simulação e aparência. Densidade/velocidade não invalidam o editor; materiais não obrigam nova leitura do DXF.
- Cache derivado de geometria em JSON comprimido, validado e recuperável. Cache inválido volta ao leitor original; nenhum formato executável é carregado. Mapeamentos manuais de materiais permanecem prioritários.
- Os dois caches auxiliares 2D e o canvas principal continuam existentes. Invalidação por camada e reaproveitamento no pan de superfícies menores; liberação do arraste recompõe a vista exata. Superfícies grandes mantêm o caminho direto.
- Tiles locais usam identidade de projeto e fonte, mantêm detalhe anterior enquanto carregam e rejeitam respostas de um contexto antigo. Fontes e caminho de exportação permanecem preservados.
- Controles de materiais existentes reunidos em uma janela de Cena, sem duplicar campos nem criar outro motor.

## Evidências e limites

Resultados desta revisão em `suporte/documentacao/validacao_1_42_21/`; auditoria e fontes dos testes também estão no repositório. Validação direcionada autorizada pelo usuário: não equivale à execução completa da suíte histórica.

As medições identificam cenário, resolução e limites; não demonstram ganho universal. Não foi medida RAM total/GPU. A imagem não ganha detalhe inexistente no original. O WebGL foi exercitado separadamente e mantém seu motor próprio.

Ainda pendentes: incrementalidade por objeto em todas as operações, validação nativa Windows/WebView2/OneDrive e ensaio prolongado de uso intenso. Reconstrução universal de ligações, reconhecimento semântico com pesos treinados e núcleo CAD completo continuam fora deste escopo. Não há promessa de equivalência ao Twinmotion nem certificação normativa.

Prontidão provisória para uso intenso: **7/10**. Há regressões dirigidas e exportação real verificadas, mas faltam validação nativa e carga prolongada para sustentar 9/10. A main permanece intacta.
