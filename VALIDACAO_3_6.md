# Validação da versão 3.6

Data: 02/11/2026. Ambiente local: Linux, Python 3.12, Chromium, dependências Studio/Pillow 13.0.0.

- 15 testes de integração passaram: pacote, API, geometria vetorizada, reserva física, cache de editor, busca de líder, orçamento de CPU, instante de prévia e vídeo.
- 48 testes dirigidos passaram; dois casos fora do recorte foram deselecionados (endpoint completo de preparo DXF e relatório de simulação de 120 s).
- MP4 sintético HD 1280×720, 24 fps, 3 s: 72 quadros decodificados integralmente, H.264/yuv420p, sem erros.
- Chromium: nove painéis em quatro resoluções; abrir/fechar não alterou o retângulo do canvas nem a vista. Aplicar salvou sem fechar; descartar restaurou a base aplicada; cancelar e arrastar funcionaram; ferramentas e linha de comando não deslocaram a área gráfica.
- Reabertura de projeto temporário com artefatos realmente atuais: nenhuma nova requisição de análise ou atualização. Instantes fracionários e troca de duração curta/longa foram preservados.
- Comparação 3.5.1 × 3.6: três repetições; todos os arrays de quadros da simulação sintética foram iguais. Tempos e escopo em proveniencia/medicoes-3.6.json.
- Ruff F821: nenhum nome indefinido nos módulos do aplicativo. Compilação Python executada; o empacotador verifica JavaScript com Node e hashes de todos os arquivos.

O pacote passa pelo portão original com --sem-suite: integridade, aplicação em instalação sintética, importação do servidor, componentes, restauração e servidor real. A suíte integral permanece sem aprovação; consultar PENDENCIAS_3_6.md. Os workflows remotos executam as verificações do Studio, incluindo o cenário de janelas no Chromium.

Não foram medidos FPS de GPU, tempo do empreendimento inteiro nem o computador do usuário. Windows/WebView2 não foi exercitado localmente. Planejamento de núcleos não é garantia universal de utilização de CPU ou de tempo de conclusão.
