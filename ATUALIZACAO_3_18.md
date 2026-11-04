# Rodovia Studio 3.18

Atualização do aplicativo existente. O DXF original não é reescrito.

## Motor e exportação

Na confluência, a aceleração considerava a folga de aproximação, mas a limitação final do avanço admitia apenas a distância física mínima. O motor agora reserva espaço antes de cada passo, incluindo o conflito previsto na confluência e a faixa de destino de uma troca. Fora dos controles permitidos, usa margem de 12,5 m ou dois segundos de velocidade, mais tolerância. A auditoria independente permanece ativa: nenhuma violação é apagada para liberar o resultado.

A simulação inteira é conferida antes da codificação. Uma falha física tardia deixa de consumir milhares de quadros do MP4; o vídeo anterior é preservado. **Preparar Rodovia Studio** passa a ser a ação principal; **Gerar vídeo**, a seguinte. A preparação conserva geometria e editor válidos mesmo se a frota reprovar. A simulação preparada é reutilizada quando a chave de projeto/motor não muda.

Em Veículos e fluxo, **Faixa final sem veículos** tem padrão de 25 m e dissolução antes desse limite, considerando a frente do veículo. O limite pertence ao fim do itinerário completo, não às ligações internas, e não constitui uma parede física. Zero desativa esse recorte.

O padrão de exportação continua estrito. A opção explícita **Operação parcial** faz a validação integral e retira da apresentação todos os veículos dos itinerários reprovados, em toda a duração, identificando o resultado. Colisões físicas continuam bloqueando. Essa opção não corrige a física nem elimina a auditoria.

## Comandos e apresentação

- **AUDITARMEDIDAS** separa travessia livre, distância entre apoios e altura. Preencher 12 m em FreeFlow e 18 m em Sacrifício ajusta explicitamente apoios e pontos de medição, preservando centro e orientação. Campos vazios não alteram pórticos. A atualização não aplica essas dimensões por nome a projetos alheios.
- **EIXOCONDUCAO** cria alinhamento local; **ANCORARFLUXO** estabelece origem e destino por faixa para conduzir até outra pista ou retorno. Conexões explícitas admitem distância configurável até 300 m, mantendo verificações de pavimento, tangência, nível e impedimentos. Não promove o alinhamento a referência principal. Reabrir seção unidirecional contrária conserva os sentidos.
- Dia/noite tem comando próprio com ícone de lua, aplicação persistente e sincronização do 3D aberto; clima permanece separado. Janelas de modelagem oferecem aplicar, cancelar e fechar sem deslocar o desenho.
- Juntas do concreto seguem estação e normal locais do eixo, delimitando placas transversais e longitudinais. A OAE recebe juntas e barreiras laterais de apresentação. Hachuras identificadas como TALUDE/TERRAPLENO deixam a classificação de pista e passam a terreno. Artístico continua como padrão, com realista separado.
- A defesa de sinalização impede que eixo, seta, zebrado e pintura SH (exceto bordo LBO) sejam tratados como obstáculos ou guias de bordo, mesmo se uma camada de pintura estiver indevidamente classificada. Pavimento, canteiro e obstáculos físicos continuam validados.

## Limpeza

**LIMPAR** move categorias selecionadas para quarentena restaurável. Duplicatas de vídeo são verificadas por tamanho e SHA-256 completo; vídeos referenciados e conteúdo único são preservados. **QUARENTENA** permite restaurar sem sobrescrever destinos existentes. **SANITIZAR** apresenta o inventário da instalação; a limpeza da instalação usa o comando existente com o aplicativo fechado.

A retenção mínima é de 30 dias desde a entrada em quarentena. A exclusão ocorre na abertura ou a cada 12 horas enquanto o aplicativo estiver aberto; não há serviço que apague arquivos enquanto fechado. Esta revisão não executou limpeza na máquina do usuário.

Ajuda atualizada em F1/AJUDAVERSAO, incluindo os comandos e limites desta revisão. Consulte [a validação](VALIDACAO_3_18.md).
