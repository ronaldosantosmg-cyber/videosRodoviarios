# Validação 1.42.26

54 testes dirigidos aprovados nesta revisão (50 de interface/integração/atualização e 4 de vídeo/snapshot). O teste de contrato foi reexecutado após tornar a referência histórica independente do Git (um teste adicional, não somado aos 54).

Preservados 477 identificadores e 227 campos/canvas. Chromium real em quatro resoluções, integração com worker, proposta/revalidação/desfazer, proteção de configuração, WebGL, captura e exportação 3D. MP4 2D: H.264, 1280×720, 24 fps, 72 quadros decodificados em cada ensaio de materiais e dois processos, sem erros de decodificação.

DXF real: 31 eixos, 6 fluxos e 6 revalidados, original preservado, prévia neutra HD em 41,33 s. É ensaio identificado, não ganho comparativo ou conformidade de qualquer projeto.

Compilação com/sem WebView2 e splash em Mono/Xvfb. Isso não equivale à validação completa da GUI Windows. Consulte a evidência separada de GitHub Actions quando disponível para o escopo nativo.

Firefox: download bloqueado por política de rede, HTTP 403. Edge nativo não executado. A interface usa recursos nativos e bibliotecas locais existentes, sem plugin novo; o motor/servidor continua necessário para cálculos e vídeo.

A auditoria estática não prova ausência de malware nem desfaz o alerta corporativo. O index.html foi reestruturado; o núcleo 00_nucleo.js permanece utilizado. Não há mudanças de evasão do antivírus, restauração automática ou exclusões.
