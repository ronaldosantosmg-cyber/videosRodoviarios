# Rodovia Studio 1.40.6 — Qualidade visual automatizada

## O que foi implementado
- Harness Playwright offline usando o `index.html`, CSS e módulos JS reais.
- Testes visuais de shell, viewport dominante, painéis encaixados, gaveta de comando, modo Projeto e resolução 1366×768.
- Capturas automáticas em `resultados_testes_visuais/`.
- Detecção de erros JavaScript/console durante os cenários.
- Verificação de ausência de nomes de rodovia/empreendimento fixos na tela inicial.
- `TESTAR INTERFACE.cmd` para execução local.
- Fallback offline para ambientes em que políticas corporativas bloqueiam `localhost` no Chromium.

## Critério
Os testes medem geometria real no navegador: painéis não podem sobrepor o viewport; abrir uma gaveta deve reduzir a área gráfica; F11 deve ampliar a área; e a interface não pode gerar erro JS no fluxo testado.

## Observação
A suíte integrada com o servidor continua disponível. A suíte 1.40.6 não depende de rede nem de `localhost`, então consegue rodar inclusive em ambientes corporativos restritos.
