# Rodovia Studio 3.3

Melhorias trazidas do GeoVias 1.0 (mesma base 3.2.1):

- **Sinalização:** linhas fantasma não cortam mais sinalização real que corre dentro do pavimento nem a de dispositivos longe do eixo (rotatórias, alças) — `fantasmas.py`.
- **Fluxo:** corredor povoado em toda a extensão no primeiro quadro; em pista sem ultrapassagem os veículos têm velocidades ligeiramente diferentes (sem comboio); pelotões só em parada controlada. Ajustes em `Settings`: `traffic_semear`, `traffic_sem_comboio` (ligados por padrão). Relatório com `desempenho_corredor`.
- **DXF:** leitura tolerante (modo de recuperação do ezdxf), blocos quebrados ignorados com aviso, conferência de unidade, eixo sem extensão ignorado e avisado, preparo automático ao abrir (variável `RODOVIA_PREPARO_AUTO`; original preservado em `input.antes_preparo.dxf`).
- **Mapa:** cache de ladrilhos mantém imagem de zoom menor enquanto a nítida carrega (sem zonas pretas).

Não executado: gate completo (`validar_entrega.py`); sem teste em Windows/WebView2.

## 3.4 (complemento)
- Menus por finalidade, painéis, barra de comandos e canvas fluido (portados do GeoVias).
- Filas só em semáforo/travessia/pare-e-siga, com verde mínimo e regra de caixa; semeadura segura.
- Abertura mais rápida (import tardio de imagens: partida 2,7→0,9 s; RAM ~153→103 MB), log sem inundação, Scene() ~60→34 s no DXF de teste.
- Testes de layout antigos (faixa/ribbon) ficam obsoletos com os novos menus, como no GeoVias.

## 3.5 — correção da prévia que levava ~1 hora
Causa (log do usuário, 02/11): a semeadura inicial de veículos (3.3) comparava cada veículo com todos os já semeados (O(n²)) e a prévia simulava os 180 s do vídeo + 90 s de aquecimento, mesmo mostrando só o instante 30 s.
- Semeadura com índice espacial (grade de 50 m) — antes >150 s para ~1300 veículos, agora ~35 s.
- Prévia em vista geral (veículo < 1 pixel): simulação dispensada; diagnósticos da última simulação completa são mantidos. Medido no DXF do usuário: >3400 s → ~48 s.
- Prévia com zoom: simula só até o instante mostrado, semeia só o entorno do enquadramento, sem ensaios opcionais de acostamento.
- Rastro de carreta (articulado.py) e varredura de veículos (vehicle_safety.sweep) vetorizados — resultados idênticos (12.473 comparações sem diferença).
- Vídeo final: comportamento da simulação inalterado.
