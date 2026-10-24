# Rodovia Studio 1.40.9 — Validação ampliada

Revisão focada em qualidade, sem alterar regras técnicas do projeto.

## Testes visuais ampliados
- Logo em tema claro/escuro e modo Projeto.
- Matriz responsiva 1920×1080, 1600×900, 1366×768, 1280×720 e 1024×768.
- Painéis sem sobreposição do viewport.
- Atalhos repetidos e stress de layout.
- 100 regenerações preservando câmera/zoom.
- Seleção de múltiplos objetos coincidentes.
- Estados KMZ: necessário, em uso e referência.
- Ordem explícita de ortofotos.
- Política de ultrapassagem nas propriedades da rota.
- Recuperação após comando inválido.
- 100 ciclos de painéis sem deriva.
- Ausência de overflow horizontal.
- Logo preservado após stress de F11.

## Testes funcionais
- KMZ como eixo fallback e referência geográfica/POIs.
- KMZ inválido falha fechado com mensagem.
- Salvamento atômico preserva configuração anterior em erro.
- Tráfego pesado forma/dissipa fila sem colisões.
- Mudança de faixa exige a manobra inteira dentro da zona permitida.
- Workspace permanece genérico e sem projeto/rodovia hard-coded.
- Compilação de todas as fontes Python.

## Resultado executado
- 12/12 testes visuais novos.
- 22/22 regressões visuais recentes.
- 38/38 testes técnicos/regressões recentes.
- 7/7 workflows completos de API/processamento.
- Python compileall: OK.
- JavaScript node --check: OK.

## Regressões encontradas e corrigidas
1. Em 1280/1366 px, dois painéis simultâneos podiam reduzir demais a área gráfica. Agora são mutuamente exclusivos até 1400 px.
2. Uma seleção antiga podia tentar calcular sua barra gráfica sem metadados de imagem carregados. Agora a rotina falha de forma segura e não derruba a interface.
