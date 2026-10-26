# Rodovia Studio 1.42.19

Correções do log de uso e continuidade da revisão 1.42.18. Entrega com validação direcionada; não certifica uso intenso em Windows.

## Densidade e erros de uso

- Exportar vídeo → Tráfego: o botão **Usar densidade** retira a demanda explícita e habilita a densidade entre 0,2 e 8. Demanda explícita mantém prioridade enquanto preenchida. Salve e gere a prévia ou reconstrua o 3D para atualizar veículos. Densidade não habilita rotas inexistentes ou inseguras.
- Corrigido `KeyError: 'oae'` ao pintar concreto de OAE, nos estilos artístico e técnico. Materiais de outros tipos não entram indevidamente no pintor de pavimento.
- Importação recebe a revisão nova da configuração, preservando edições e histórico. Gravações em fila coletam os valores atuais quando realmente começam. Conflitos sem sobreposição são mesclados; alterações concorrentes no mesmo campo permanecem bloqueadas, sem sobrescrever outra janela.
- Recálculo automático espera janelas de edição e importação de arquivos, inclusive quando a janela abre durante a gravação. Não inicia vídeo sozinho.
- Leitura KML/KMZ incremental, sem expandir anexos, com limite de 256 MiB de XML e um milhão de coordenadas. Caminhos inseguros, DTD/entidades, estruturas excessivas e não finitos continuam recusados. A referência exata de 146,9 MB do usuário não foi fornecida; foi testado XML sintético de aproximadamente 147 MiB.
- Redimensionamento 2D/3D agendado por quadro, sem alterar dimensões do canvas dentro da notificação do ResizeObserver. Redimensionamento 3D não realimenta as dimensões CSS pelo buffer de desenho.
- A central de fluxos abre orientações mesmo sem trajetórias. Seleção de área sem polígono fechado explica a necessidade de clicar no interior ou desenhar o contorno; falhas HTTP diferentes não são mascaradas como ausência de área.

## Reconstrução e precisão

**Corrigir fluxos → Reconstruir ligação contínua** tenta reparar a derivação do fluxo, preservando extremidades e progressão. Revalida largura, superfície, corpo e movimento. Limites: 5 km por tentativa, sete escalas de suavização e desvio máximo de 8 m. Não altera o DXF, não atravessa barreiras ou superfícies desconectadas, não recompõe cortes explícitos nem reativa desligamentos manuais. A recuperação por exclusão continua disponível. Auto-interseções ambíguas e ligações sem solução segura ainda exigem edição; não há garantia de reconstruir qualquer rede.

Arcos, linhas, segmentos com bulge e NURBS preservam uma representação paramétrica junto às linhas de seleção. Comprimentos circulares são analíticos; comprimento e projeção de NURBS usam métodos numéricos. A seleção consulta a curva nativa e não somente as cordas desenhadas. Eixos têm tesselação de apresentação mais fina. Translação/rotação/escala uniforme preservam a curva; reprojeção não linear remove o descritor para não anunciar precisão falsa. Ainda não é um núcleo completo como AutoCAD: recorte, interseções e edição exata de todas as curvas precisam de próximas etapas.

## Reconhecimento de imagem: capacidade condicional

Há adaptador ONNX local, conectado à análise e aos grupos existentes. Usa CPU, confere hash dos pesos, dimensões, normalização, classes e presença de avaliação independente por classe; rejeita baixa confiança e transparência. Não baixa pesos, envia imagens ou executa scripts. Objetos continuam revisáveis e não criam tráfego automaticamente.

**Nenhum modelo treinado foi incluído nesta revisão. O reconhecimento semântico permanece indisponível até instalação e avaliação de pesos adequados.** A rede do ambiente bloqueou o acesso ao repositório de modelos. Os testes do adaptador usam uma rede substituta determinística; não medem acurácia de reconhecimento de edificações, OAE ou ferrovia. A segmentação assistida já existente permanece disponível.

Instalação futura: arquivos `modelo.onnx` e `modelo.json` em `projetos/modelos/imagem_aerea/` (abaixo da pasta de dados efetiva, independente da pasta do executável). O manifesto informa `sha256`, `classes`, `input_size` (256/512/1024), `output` (`logits` ou `probabilities`), `mean`, `std`, `confidence_threshold` e `evaluation`. A avaliação identifica os mesmos pesos, conjunto independente e IoU/quantidade anotada por classe. Declarar números no manifesto não substitui executar e revisar a avaliação real. Classes sem evidência não devem ser habilitadas; fotografia não determina desnível ou restrições de tráfego.

## Entrega

Pacote exclusivamente em `atualizacoes/`; preserva projetos, vídeos, KMZ e cache persistente GeoTIFF. Snapshot, fechamento controlado e rollback conferidos no teste da atualização. Evidências e limites em `suporte/documentacao/validacao_1_42_19/`.

Nota provisória para uso intenso: **7/10**. Falta validação nativa Windows/WebView2/OneDrive, carga prolongada, calibração e avaliação do modelo semântico. Não há certificação DNIT/CONTRAN.
