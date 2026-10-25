# Painéis e correção de fluxos — 1.42.14

## Modificar / propriedades

**Salvar e fechar** aplica também os textos digitados nas propriedades que ainda não receberam Enter. Os valores são enviados pela configuração comum do motor. Erros de gravação/validação continuam visíveis e mantêm a edição aberta para correção; o programa não informa um salvamento que falhou.

Após confirmação de **Descartar**, o modelo anterior é restaurado e a janela se fecha, mesmo se uma atualização auxiliar de listas/propriedades falhar. Solicitações simultâneas compartilham uma única decisão. O painel volta ao local de origem e libera seus controles. As janelas já existentes continuam com salvar/descartar/continuar; esta correção não é a reorganização completa de tela prevista para outra revisão.

A restauração da seleção durante resize/regeneração respeita o fechamento explícito e não reabre as propriedades de fluxo. O realce da seleção é mantido; os botões de painel continuam permitindo reabrir a edição quando solicitado.

## Seleção de eixos e pequenas rotas

A lista de eixos não apresenta os menores que **Desligar fluxos abaixo de**. Alterar o limite atualiza essa lista imediatamente. A comparação usa o comprimento sem arredondamento; 49,999 m não é apresentado como elegível para um limite de 50 m. As escolhas de sentido/desativação dos eixos ocultos permanecem preservadas, inclusive ao reduzir o limite novamente.

As rotas independentes abaixo do limite continuam fora da circulação. Não são apagados DXF, projetos ou geometrias manuais. Pequenos subtrechos internos de um eixo longo não são tratados como minirrotas independentes, nem criam entradas artificiais de veículos.

Em eixos com vértices consecutivos a menos de 5 cm, a derivação pode simplificar pequenos nós com tolerância máxima de 2 cm. O original permanece intacto e a trajetória resultante continua sujeita à análise de movimento e pavimento. O processo não libera curvas maiores inviáveis, obstáculos, lacunas ou movimentos proibidos. As identidades anteriores são conservadas; uma desativação de eixo já unido continua válida após recalcular.

## Assistente técnico local

Selecione o fluxo com problema e abra **Como corrigir este fluxo · assistente local**. O assistente explica a causa, orienta os passos e informa o motivo de cada recomendação. Quando aplicável, oferece **Localizar ponto**, **Abrir camadas** e **Recalcular fluxos**, sempre por solicitação do usuário.

É um **sistema especialista local baseado em regras e nos diagnósticos geométricos**, não um modelo de linguagem treinado ou uma IA que aprende sozinha. Não envia o desenho, coordenadas ou logs para serviços externos. O modo IA de geração de prompt permanece separado.

Para falta de pavimento: localizar o ponto, conferir papéis de camadas e corrigir hachura/faixa. Para curvas, ziguezague e auto-interseção: revisar os pontos de controle e, se adequado, usar a recuperação existente para manter apenas partes revalidadas. Para falha de conexão: conferir pontas, nível e sentido, ou definir uma rota contínua explicitamente. Não recomenda reativar automaticamente uma decisão manual nem reduzir o limite global para habilitar fragmentos isolados.

Instale por `atualizacoes/` e use **Calcular e atualizar fluxos** para obter os novos diagnósticos. As evidências registram o conjunto direcionado de testes e seus limites; a suíte integral não foi repetida, conforme o fluxo simplificado solicitado. Não houve validação nativa Windows/OneDrive/WebView2 nem certificação normativa.
