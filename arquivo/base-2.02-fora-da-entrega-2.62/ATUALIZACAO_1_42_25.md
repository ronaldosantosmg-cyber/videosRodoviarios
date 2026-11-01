# Rodovia Studio 1.42.25 — segurança, proteção e execução assistida

## Bloqueio relatado

A revisão 1.42.24 teve bloqueio relatado pelo antivírus corporativo. Não foram fornecidos fornecedor, nome da detecção ou arquivo apontado. Isso não comprova nem descarta malware. Não restaurar quarentena, criar exceções ou desativar proteções. Encaminhe à TI o pacote, seu SHA-256 e as evidências de auditoria.

A auditoria de dependências identificou vulnerabilidades conhecidas no Pillow 12.3.0. Esta revisão usa Pillow 13.0.0 e pip 26.2.2. As dependências Windows estão fixadas com hashes conferidos no PyPI, incluindo dependências transitivas. Isso não significa que a vulnerabilidade tenha sido a causa do alerta.

A lista Windows e o ambiente de teste foram consultados com pip-audit, sem vulnerabilidades conhecidas após a correção. Inventário estático não encontrou os padrões proibidos examinados nem binários PE no pacote de fontes. Esses controles não equivalem a uma certificação de ausência de vírus. Os resultados específicos do Microsoft Defender/Windows ficam nas evidências e no workflow de verificação; a análise do antivírus da empresa continua necessária.

## Preparação e atualização

Não há mais execução de get-pip remoto, alteração de política PowerShell ou recompilação automática. A preparação usa Python 3.12 de origem oficial aprovado pela TI e um ambiente local, ou o runtime portátil já existente. Aceita wheels verificados por hash; não instala distribuições fonte durante a preparação Windows.

O iniciador em código-fonte passa a 1.5. O executável antigo não é substituído automaticamente: se estiver bloqueado/quarentenado, não o restaure. A TI deve conferir, compilar e assinar a nova fonte. A distribuição contém fontes e scripts legíveis, sem executável pronto nem certificado Authenticode.

Abertura e atualização usam Python; não exigem PowerShell para essas operações. Os scripts PowerShell de compatibilidade e verificação respeitam a política corporativa. O auxiliar de atualização roda fora da pasta alterada, preservando fechamento controlado, snapshot e rollback. Projeto e vídeos não são apagados. Coloque o ZIP em atualizacoes/ e utilize a atualização somente após a verificação/aprovação da TI.

## Proteção e recuperação

Projeto → Proteção e recuperação de dados. Também disponível na janela Abrir projeto, mesmo se a configuração não abrir.

Confere configuração, cópias do histórico e presença das fontes. A recuperação explícita verifica o hash da cópia e preserva a configuração defeituosa. Se faltar a pasta do projeto, não cria um projeto vazio. Se faltar a configuração de um projeto existente, usa a cópia registrada quando válida; não grava defaults sobre o último estado válido.

Fontes ausentes devem ser localizadas e reimportadas. Leitura geométrica e mídia são conferidas pelo motor; a inspeção rápida não afirma verificar todo DXF/KMZ/GeoTIFF internamente. O histórico de configuração não substitui backup externo completo dos projetos e originais.

## IA assistida de execução

Tráfego → IA assistida de execução, ou comando IAFLUXOS.

1. Atualize o diagnóstico quando solicitado.
2. Localize o trecho e escolha Analisar e propor correção.
3. O aplicativo fornece a geometria e as regras locais escolhem a ação permitida. O motor calcula uma prévia isolada sem alterar o projeto.
4. Confira original e trajetórias revalidadas. Confirme para aplicar.
5. Use Revalidar resultado. O programa distingue correção aplicada de conflito resolvido.
6. Desfazer correção restaura a configuração anterior se não houver edições posteriores. Se houver, use o histórico para preservá-las.

Executa recuperação de partes válidas e reconstrução validada. Ajustes de afastamento continuam no motor existente. Não remove barreiras, sinais, interdições ou desligamentos manuais, nem cria ligações de contramão para eliminar avisos.

Recorte, junção, seções e edição de pontos continuam nas ferramentas manuais existentes. A assistência não reconstrói qualquer traçado e não faz correções arbitrárias de cálculo. Quando não há solução aprovada, orienta edição manual. Não há LLM instalado, treinamento automático, envio externo ou execução de código de outra IA. Exportar prompt/importar resposta continua como complemento revisável.

## Modo CAD compacto

Na navegação superior, use Alternar modo CAD compacto. As ações principais passam a ícones com nomes por hover/foco. A estrela permite escolher até oito favoritos. A preferência fica no navegador e não muda os cálculos do projeto. O modo anterior continua disponível. Atualização, coordenadas e progresso permanecem compactos no rodapé.

## Segurança adicional e limites

Snapshots transitórios da renderização paralela recebem autenticação HMAC com chave somente da sessão. Conteúdo alterado é recusado antes da desserialização; isso é separado do histórico de recuperação do projeto.

Operações do servidor recusam origens externas e portas locais diferentes. Propostas são vinculadas ao projeto, configuração, motor e conteúdo das fontes. Uma proposta obsoleta não pode ser aplicada. A prévia assistida limita fontes a 512 MiB e 10.000 arquivos; projetos maiores usam edição manual e cálculo normal.

Consulte as evidências atuais. Não há certificação CONTRAN, garantia universal de estabilidade, assinatura digital de distribuição ou teste prolongado de OneDrive. Verificação Windows de backend/Defender não equivale a ensaio completo da interface WebView2 e de todos os equipamentos da empresa.
