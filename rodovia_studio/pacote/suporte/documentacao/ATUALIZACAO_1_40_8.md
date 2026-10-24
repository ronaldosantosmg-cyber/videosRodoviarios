# Rodovia Studio 1.40.8 — KMZ protegido e rastreável

## Objetivo
O KMZ/KML continua sendo um input técnico opcional, mas nunca é ignorado silenciosamente.

## Estados registrados por análise
- `present`: arquivo está no projeto.
- `read_ok`: ZIP/KML e coordenadas foram lidos sem erro.
- `used`: participou efetivamente da análise.
- `required`: foi indispensável, por exemplo como eixo fallback.
- `uses`: lista de usos (`eixo_fallback`, `georreferenciamento`, `pois`, `referencia_geometrica`).

## Proteções
1. KMZ presente e inválido interrompe a análise com mensagem clara.
2. Sem eixo CAD, uma linha KMZ válida pode assumir o eixo e isso fica explicitamente registrado.
3. Com eixo CAD, linhas KMZ participam da conferência de georreferenciamento.
4. POIs do KMZ permanecem disponíveis ao renderizador.
5. A interface mostra se o KMZ é necessário, está em uso ou apenas validado como referência.
6. Ao retirar um KMZ usado/necessário, a confirmação alerta que a próxima análise pode falhar ou mudar.
7. Alterar/retirar o KMZ continua invalidando `analysis.json`, forçando novo cálculo.

## Compatibilidade
Não altera o formato dos projetos. `input.kmz` continua no mesmo local e permanece em Salvar como/Exportar pacote.
