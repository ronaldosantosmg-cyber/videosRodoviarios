# Evidências 1.42.25

137 testes únicos aprovados na última execução de cada caso, sem falhas ou ignorados. O XML consolidado combina as execuções dirigidas desta revisão, sem afirmar execução da suíte histórica completa. Uma regressão de nome acessível foi corrigida e retestada; logs e primeira execução preservados.

Inclui: proteção/recuperação, falhas de disco/gravação/permissão simuladas, arquivos e fontes ausentes, proposta/apply/revalidação/desfazer pelo motor real e pela interface, desligamento manual, barreira física, fonte alterada mantendo tamanho/data, cancelamento, ações não cadastradas, modo CAD/favoritos, leitura KMZ, limite/demanda, cache corrompido, atualização/rollback, materiais e vídeo.

Vídeos reais H.264 de 1280×720, 24 fps, 72 quadros decodificados. Um ensaio usa dois processos e snapshots autenticados; outro exercita materiais e construção 3D. Não é teste prolongado ou equivalência ao Twinmotion.

DXF real disponível: 31 eixos e 6 fluxos revalidados, original preservado e prévia HD. 41,65 s nesta execução, sem afirmação de ganho percentual. Não é o projeto atual salvo do usuário.

Dependências: 36 wheels Windows com hashes conferidos no PyPI; auditoria final sem vulnerabilidades conhecidas. Pillow e pip foram atualizados. Inventário estático não substitui antivírus. O Microsoft Defender aprovou o pacote de fontes no workflow Windows; conferir commit/etapas em windows_ci.json e nos links. A compilação nativa teve um erro de caminho no ensaio e foi corrigida para caminho absoluto; somente considerar a execução posterior para esse resultado.

Verificação do ZIP, início fora da raiz, encerramento controlado, preservação de projetos/KMZ/GeoTIFF/vídeos/perfis e rollback byte a byte: verificacao_pacote.json. O documento é produzido após testar o ZIP e fica no repositório.

Permanecem pendentes: identificação do alerta corporativo, aprovação da TI, assinatura Authenticode e atualização com assinatura assimétrica, teste completo WebView2/OneDrive e carga prolongada. Backend/Defender no Windows não equivalem a validar toda a aplicação em qualquer PC. Prontidão provisória: 7,5/10.
