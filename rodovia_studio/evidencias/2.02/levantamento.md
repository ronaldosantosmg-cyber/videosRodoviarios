# Missão 2.02 — reconstrução integral

Base 2.01 (fd4ca250b3446337e3a02fe9f0ee427b070069f3), branch desenvolvimento/rodovia-studio-1.42. Main não autorizada para alteração.

Falha identificada: flow_reconstruction só suavizava uma trajetória cujo eixo já estivesse coberto pela superfície. TrafficNetwork chamava recuperação após separar as amostras inválidas. AssistedExecution aceitava existência de circulação parcial sem provar um itinerário integral.

Correção: solver com busca limitada no corredor, tentativa antes do recorte, reconstrução estrita sem fallback silencioso para partes, prova de itinerário completo por origem/sentido, proposta reversível, causas localizáveis e apresentação distinta do original/derivado. Não substitui motor, cadastro de eixos ou controle de circulação.

Infraestrutura de testes: conftest agora separa RODOVIA_DATA por worker antes de importar o aplicativo. Evita que o startup de uma instalação de teste marque tarefas de outro worker no mesmo banco como interrompidas. Mudança somente de testes; requer regressão completa nova. Não reutilizar aprovação da 2.01.

Limites e modo de uso constam em pacote/ATUALIZACAO_2_02.md. Projeto salvo específico do usuário e Windows nativo continuam ausentes desta comprovação.

A execução de desenvolvimento em entrega/ foi interrompida deliberadamente antes de aprovar pacote para acrescentar a recusa de propostas sem reparação efetiva (aviso de frota/configuração com geometria já contínua). A aprovação deverá vir de uma execução completa nova, em entrega-final/. Nenhuma aprovação antiga pode ser transferida após essa alteração de produto.
