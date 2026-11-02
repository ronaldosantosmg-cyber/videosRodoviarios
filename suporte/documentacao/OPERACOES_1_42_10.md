# Operações da revisão 1.42.10

## Fluxos

Na barra técnica, grupo **Fluxos de tráfego**, use os ícones com ajuda ao passar o mouse:

- **Apagar intervalo do fluxo**: clique início e fim no mesmo segmento. Exclui somente a circulação daquele intervalo, sem apagar o DXF. Cortes são vinculados à identidade geométrica da origem; uma alteração de traçado exige nova conferência.
- **Juntar subsegmentos**: clique no primeiro e no segundo, na ordem do fluxo. A junção usa a geometria completa. Pontas a mais de 20 m, níveis diferentes, contramão explícita, trajetórias fora da pista ou que falhem na análise de movimento não são liberadas. Os segmentos anteriores ficam desativados e uma rota única é criada. Desfazer restaura os dados anteriores.
- **Recuperar fluxo principal…**, nas propriedades: tenta uma suavização derivada limitada a 0,5 m, preservando a ordem de progressão e revalidando o corpo do veículo. Se não resolver, localiza falhas com margem, exclui esses intervalos e revalida as partes restantes. O eixo CAD não é alterado. O limite mínimo do projeto e as desativações manuais são respeitados. Lacunas não recebem atalhos nem veículos atravessando o defeito.

No estudo técnico, bolas vermelhas indicam pontos para revisão. Verde indica partes recuperadas, vermelho partes excluídas e amarelo uma recuperação parcial. Setas indicam sentido único ou duplo. Esses realces são de edição e não saem no vídeo. Uma recuperação parcial pode interromper a circulação entre as partes; não garante continuidade do início ao fim.

## Ferrovia, iluminação e semáforos

Escolha **Ferrovia → Selecionar rota de tráfego em tela**, clique na trajetória e então escolha modelo de carga ou passageiros, linha simples/dupla, sentido, ativação e composição de 5 a 100 vagões. A geometria ferroviária continua sujeita à validação de curvas. Também é possível usar uma linha DXF ou alinhamento já selecionado.

A iluminação do 3D alterna dia, entardecer e noite. Os faróis ferroviários acendem à noite, com feixe de luz; o vídeo 2D segue o modo noturno configurado no projeto. Os semáforos têm braços projetados, lentes e realce de leitura em planta/3D. O relógio em planta acompanha o tempo selecionado da prévia e os links de onda verde. Os halos facilitam a leitura; não são cálculo luminotécnico.

Passagens ferroviárias não retêm o fluxo quando o desnível declarado é diferente. Em OAE com cota não nula, o motor confere a área e o alinhamento da obra para distinguir a via elevada da transversal. Cota desconhecida ou geometria ambígua não é tratada como prova de separação. A vista não certifica gabarito vertical nem substitui levantamento.

## Materiais e nomes CAD

No grupo **Áreas e sinalização**, abra **Materiais, símbolos e nomes CAD**. Há 32 materiais procedurais locais com amostra. Use **Reconhecer nomes do DXF** para classificar nomes novos sem substituir as classificações existentes; confira o resultado antes de recalcular. Para cadastrar aliases, informe um perfil, padrão de nome, classe e material. O perfil fica salvo para outros projetos.

O padrão reconhece OAE/concreto, polígonos de árvores, hidrologia, ferrovia, Gasmig/gás, postes/rede elétrica, edificações, offset/off set/gabião como terrapleno, erosão, cortina atirantada, fibra óptica, radar e torre. Os materiais incluem solos, rochas, enrocamento, biomanta, telhas, alvenaria e madeira. Os símbolos e volumes sem cotas explícitas usam dimensões ilustrativas identificadas no modelo. Não representam cadastro de profundidade de tubulações, altura levantada de postes ou volumes de terraplenagem.

Os dados ficam na configuração do projeto e nos perfis locais. Não dependem de download de texturas. Projetos antigos mantêm suas classificações explícitas; aplique o reconhecimento quando quiser incorporar nomes adicionais. O catálogo oferece salvar, descartar ou continuar ao fechar com alterações pendentes.
