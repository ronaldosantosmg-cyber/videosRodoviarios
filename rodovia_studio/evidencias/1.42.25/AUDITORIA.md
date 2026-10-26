# Auditoria 1.42.25

Base: 1.42.24, b16d26ec3ec1925293d924a41debed6194485a3e. Trabalho na branch desenvolvimento/rodovia-studio-1.42; main não autorizada.

## Achados e correções

- Relato de bloqueio corporativo sem identificação de arquivo/detecção: causa não determinada. Não afirmar malware removido ou falso positivo confirmado.
- Pillow 12.3.0: 37 avisos conhecidos no levantamento do PyPI/pip-audit. Atualizado para 13.0.0. O pip 25.0.1 do ambiente também tinha 12 avisos e foi atualizado para 26.2.2. Ver IDs em dependencias_corrigidas.json e auditorias finais.
- Preparação anterior executava get-pip baixado, usava ExecutionPolicy Bypass e podia recompilar o iniciador automaticamente. Removidos esses comportamentos. Não há alteração de proteções do sistema.
- Windows recebe lock de 36 wheels, incluindo pip, com hashes comparados aos metadados do PyPI. O pacote não redistribui esses binários. Preparação exige Python aprovado e wheels; runtime existente continua suportado.
- Abertura/preparação/atualização por Python aprovado, com detecção de runtime portátil e venv normal. Auxiliar roda fora da instalação para permitir troca e rollback.
- Snapshots IPC de vídeo paralelizado usavam pickle sem autenticação. Agora a chave não é gravada no disco e o conteúdo é verificado antes da desserialização. Não se importam snapshots pickle externos.
- Salvamento com configuração ausente podia inicializar outro estado apesar do histórico. Agora recupera a última configuração registrada antes de salvar. Permissão negada não é tratada como corrupção; não substitui arquivo válido.
- Configuração e índice corrompidos podem ser recuperados explicitamente por cópia com hash e modelo validados. A configuração defeituosa fica arquivada. Fontes ausentes são indicadas e não recriadas vazias.
- Propostas de fluxo calculadas em sandbox, por Scene.light e o motor existentes. Só ações permitidas de recuperação/reconstrução, revisão, confirmação, aplicação, nova validação e desfazer com proteção contra edições posteriores.
- UI CAD opcional e favoritos reaproveitam os mesmos comandos. Nenhum cálculo inicia por escolher ícones.

## O que não foi declarado implementado

Não há diagnóstico de qualquer malware, assinatura Authenticode, atualização com assinatura assimétrica, backup externo completo, reconhecimento semântico autônomo de imagens, solução universal de conflitos, IA treinada ou reparo automático arbitrário. Recortar/juntar e configurar seções continuam manuais na central existente. Recuperação confere configuração; inspeção rápida das fontes confere presença, enquanto integridade geométrica/mídia depende do motor.

O modo IA é um especialista local de regras sem instalação adicional. Não executa código externo ou envia logs/projetos a serviços de IA. O caso real usa o DXF disponível, não o projeto atual salvo do usuário.

## Validação e rastreabilidade

Regressões e XML desta revisão, MP4 decodificado, imagens e relatórios atuais neste diretório. O XML consolidado conserva a última execução de cada caso; tentativas e correções ficam nos logs. Uma falha de nome acessível causada pela adaptação a ícones foi corrigida e reexecutada. Ensaios Windows ficam vinculados ao commit e workflow: testes de backend e Defender não equivalem à validação completa WebView2/OneDrive.

A única medição real de DXF desta revisão está em dxf_real.json. Não foi demonstrado ganho percentual de desempenho; a comparação usa hardware/condições variáveis. Prioridade foi segurança e integridade.
