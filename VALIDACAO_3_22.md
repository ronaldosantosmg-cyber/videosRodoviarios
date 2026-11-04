# Validação 3.22

## Testes dirigidos

49 aprovações no conjunto:

- `test_slab_width_texture.py`
- `test_convoy_warning_export.py`
- `test_validated_presentation.py`
- `test_traffic_pipeline.py`
- `test_video_pipeline.py`
- `test_artistic_reference_materials.py`
- `test_concrete_rock_reference.py`
- `test_hatch_material_inheritance.py`
- `test_surface_joint_geometry.py`
- `test_terminal_presentation.py`
- `test_gold_guidance.py`

Conferências relevantes:

1. O diagnóstico informado pelo usuário (percurso 1, estação 135,37 m, 202 s, folga 8,088 m e restante 432,1 m) não lança mais exceção de exportação. O registro permanece inalterado.
2. Exportação real de MP4 com 3 s/72 quadros e diagnóstico injetado, mantendo posições físicas. Arquivo final produzido, decodificação aprovada e diagnóstico preservado em `video.json`.
3. Colisão física frontal/lateral e simulação incompleta continuam bloqueando.
4. Aviso tardio nos checkpoints não impede conclusão; cancelamento/retomada, cache frio/quente e equivalência dos estados físicos permanecem testados.
5. MP4 com dois processos e validação de todos os quadros; falha física antes da composição preserva o resultado anterior.
6. Juntas de placas com largura configurada de 4 m, em referência de eixo e centro de faixa, sem preencher os vazios; dimensões inválidas rejeitadas.
7. Texturas artísticas/realistas, concreto/rocha, OAE, materiais por hachura, juntas orientadas e máscara de 25 m preservados.

## Interface real

- `scripts/verificar_materiais_areas.py`: aprovado em Canvas/Chromium, materiais locais/automáticos, textura própria, vazios e separação de materiais no mesmo layer.
- `scripts/verificar_janelas.py`: aprovado em quatro resoluções, com menus acessíveis e rascunhos preservados, Aplicar/Cancelar/Descartar/Fechar e persistência de iluminação.

Os testes dirigidos foram executados em Linux/Python 3.12. A suíte histórica integral não foi executada. O caso de 202 s foi usado como diagnóstico de teste: não se alega ter reproduzido e corrigido sua causa física exata no projeto do usuário. A geração do vídeo e a eliminação de comboios no motor são critérios distintos.

Não foi executado Windows/WebView2/Defender. A condição antimalware segue pendente conforme documentado na 3.21. Os testes de integridade e instalação não substituem análise do antivírus.
