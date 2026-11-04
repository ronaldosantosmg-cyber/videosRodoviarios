# Evolução técnica baseada no Rodovia Studio 3.16

Esta ramificação não substitui o aplicativo instalado. A versão principal 3.16 segue intacta.

## Requisitos consolidados
1. **Sinalização:** separar linhas de bordo, divisórias e barreiras físicas por segmento, inclusive quando compartilharem o layer; pintura contínua restringe manobras mas não é colisão física. Ambiguidades exigem revisão.
2. **DXF universal:** reutilizar dxf_preparo.py e layer_profiles.py; não alterar original; permitir perfis de interpretação por projetista e validar a geometria.
3. **Sentido individualizado:** identificar eixo principal elegível de maior extensão, usar km inicial/final como referência, e manter escolha de fluxo exclusiva de cada eixo. Operações em uma rota não podem alterar os outros eixos.
4. **Interface:** painéis e abas sobrepostos sem alterar tamanho de viewport, câmera ou zoom; evitar tremor; interface pública em português, exceto comandos CAD conhecidos; ajudas contextuais curtas.

## Código implementado nesta etapa
- Módulo independente traffic_marking_policy.py: autorização conservadora de cruzamento e atualização imutável de seleção por eixo.
- Testes em tests/test_traffic_marking_policy.py.

## Integração pendente
- Conectar as regras ao detector de geometrias, editor de fluxos e motor de tráfego. Atualmente as novas funções **não são chamadas pela simulação**.
- Revisar precedências existentes em direction_policy.py, onde uma rota cadastrada pode sobrepor a escolha do eixo.
- Implementar os painéis sobrepostos e testar a preservação exata de dimensões, centro, zoom e câmera.
- Executar testes completos de regressão, testes de navegador e geração de vídeo em Windows antes de publicar uma atualização.

Teste isolado: python -m pytest -q tests/test_traffic_marking_policy.py
