# Rodovia Studio 3.19

Reforço da regra de ouro no motor existente, sem criar outro aplicativo ou alterar a geometria do DXF.

## Controle de admissão nas confluências

Antes de admitir um novo veículo, o motor verifica espaço na ligação de destino e a aproximação pelos acessos concorrentes. Também reserva folga para um veículo parado no acesso lateral: sua velocidade baixa não pode fazê-lo desaparecer da previsão de risco.

Se faltar espaço, a demanda permanece pendente fora do modelo e a tentativa daquele itinerário é adiada em 0,6 segundo **de tempo simulado**. Não existe espera de relógio, `sleep` ou ciclo extra de aquecimento. Os veículos existentes seguem o motor normal; não são removidos, recuados ou marcados com uma preferência inexistente. A regra de ouro e a validação antes do MP4 permanecem ativas.

## Custo controlado

- Confluências de até 120 m da entrada são indexadas uma vez ao preparar a simulação. Não se inspecionam todos os itinerários a cada passo.
- A ocupação ordenada já existente fornece até dois vizinhos na ligação de destino por busca binária e o primeiro veículo de cada acesso concorrente.
- Percursos sem confluência próxima não consultam essa ocupação. Após uma retenção, a próxima tentativa respeita o intervalo simulado de 0,6 s.
- Não há aumento no aquecimento configurado, no número de passos físicos ou no trabalho por quadro do vídeo.
- As reservas durante o movimento continuam protegendo ligações mais distantes; esse controle local de entrada é uma proteção adicional, não a substituição da física ou da auditoria.

O relatório da simulação acrescenta `confluence_admission`, com verificações, retenções e consultas a vizinhos. Não há novo comando obrigatório: a proteção é automática. Atualize, execute **Preparar Rodovia Studio** e depois **Gerar vídeo**. A alteração do motor invalida uma vez o cache físico antigo, para não reutilizar resultados anteriores à proteção; resultados seguintes podem voltar a ser reutilizados.

Consulte [os testes e tempos medidos](VALIDACAO_3_19.md). As funcionalidades e correções da 3.18 são mantidas.
