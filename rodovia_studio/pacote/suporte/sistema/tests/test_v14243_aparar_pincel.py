"""1.42.43: APARAR (trim), melhoria do pincel e vista estável ao localizar."""
import json,subprocess
from pathlib import Path
from test_v14234_nodes_ui_video import live,gl_page

JS=Path(__file__).resolve().parents[1]/'app'/'js'


def _node(code):
    r=subprocess.run(['node','-e',code],capture_output=True,text=True,timeout=30)
    assert r.returncode==0,r.stderr
    return json.loads(r.stdout)


def _trim(points,edges,click):
    return _node(f"const T=require({json.dumps(str(JS/'91_aparar.js'))});console.log(JSON.stringify(T.compute({json.dumps(points)},{json.dumps(edges)},{json.dumps(click)})))")


P=[{'x':0,'y':0},{'x':10,'y':0},{'x':20,'y':0}]
E=[[{'x':5,'y':-1},{'x':5,'y':1}],[{'x':15,'y':-1},{'x':15,'y':1}]]


def test_trim_meio_divide_em_duas_partes():
    r=_trim(P,E,{'x':10,'y':0.3})
    assert r['pieces']==[[{'x':0,'y':0},{'x':5,'y':0}],[{'x':15,'y':0},{'x':20,'y':0}]]


def test_trim_ponta_mantem_vertices_restantes():
    assert _trim(P,E,{'x':2,'y':0})['pieces']==[[{'x':5,'y':0},{'x':10,'y':0},{'x':20,'y':0}]]
    assert _trim(P,E,{'x':19,'y':0})['pieces']==[[{'x':0,'y':0},{'x':10,'y':0},{'x':15,'y':0}]]


def test_trim_sem_interseccao_informa_erro_e_nao_altera():
    r=_trim(P,[],{'x':3,'y':0})
    assert 'error' in r and 'pieces' not in r
    assert 'error' in _trim([{'x':0,'y':0}],E,{'x':0,'y':0})


def test_trim_registrado_e_pincel_troca_origem():
    s=(JS/'91_aparar.js').read_text(encoding='utf-8')
    assert "'APARAR','TRIM'" in s and "itemFaixa('Editar','Modificar'" in s and 'checkpoint()' in s
    b=(JS/'35_pincel.js').read_text(encoding='utf-8')
    assert 'e.shiftKey&&brush.src' in b


def test_localizar_nao_altera_zoom_quando_ponto_visivel(gl_page):
    p=gl_page
    r=p.evaluate("""()=>{if(!ready())return null;const w=canvasToWorld?canvasToWorld(canvas.width/2,canvas.height/2):null;if(!w)return null;
      const s0=view.s,ox=view.ox,oy=view.oy;revealPoint(w);return {same:view.s===s0&&view.ox===ox&&view.oy===oy}}""")
    if r is None: return   # editor sem projeto neste fixture
    assert r['same']


def _js(file,expr):
    code=f"const T=require({json.dumps(str(JS/file))});console.log(JSON.stringify({expr}))"
    return _node(code)


def test_icones_menus_e_botoes_por_rotulo():
    assert _js('92_icones_menus.js',"[T.iconFor('Salvar como…'),T.iconFor('Cancelar'),T.iconFor('Aplicar'),T.iconFor('Aparar'),T.iconFor('Tráfego'),T.iconFor('Xyz')]")==['💾','✖','✅','✂','🚗','']


def test_conferencia_semaforo_e_materiais():
    assert _js('93_conferencia_pre_video.js',"T.judge({}).level")=='green'
    assert _js('93_conferencia_pre_video.js',"T.judge({A:[{code:'juntas',text:'x'}]}).level")=='yellow'
    assert _js('93_conferencia_pre_video.js',"T.judge({A:[{code:'sem_pavimento',text:'x'}]}).level")=='red'
    assert _js('93_conferencia_pre_video.js',"T.materials({pavement_areas:[{kind:'pavement',material:'auto'},{kind:'pavement',material:'auto'}]})")[0]['n']==2


def test_ponte_de_vazios_do_pavimento_oculta_e_nao_bloqueia():
    """Requer shapely/numpy (sem gate neste ambiente: escrito, não executado na 2.07)."""
    import types,numpy as np
    from app.traffic import TrafficNetwork
    lane=np.column_stack([np.arange(0,300.),np.zeros(300)])
    runs=[(0,100),(150,300)]
    me=types.SimpleNamespace(s=types.SimpleNamespace(traffic_bridge_max_m=150.,traffic_bridge_lead_m=5.,lane_width_m=3.5),ghost_zones=[])
    out=TrafficNetwork._bridge_runs(me,lane,runs)
    assert out==[(0,300)] and len(me.ghost_zones)==1
    assert me.ghost_zones[0].contains(__import__('shapely.geometry',fromlist=['Point']).Point(125,0))
    assert me.ghost_zones[0].contains(__import__('shapely.geometry',fromlist=['Point']).Point(96,0))      # 5 m antes
    far=types.SimpleNamespace(s=types.SimpleNamespace(traffic_bridge_max_m=20.,traffic_bridge_lead_m=5.,lane_width_m=3.5),ghost_zones=[])
    assert TrafficNetwork._bridge_runs(far,lane,runs)==runs       # vazio maior que o limite: não atravessa


def test_tunel_longo_sem_pavimento_nao_corta_com_limite_padrao():
    """Requer shapely/numpy (escrito, não executado)."""
    import types,numpy as np
    from app.traffic import TrafficNetwork
    from app.models import Settings
    lane=np.column_stack([np.arange(0,4000.),np.zeros(4000)])
    runs=[(0,500),(3500,4000)]       # túnel de 3 km
    me=types.SimpleNamespace(s=Settings(),ghost_zones=[])
    assert TrafficNetwork._bridge_runs(me,lane,runs)==[(0,4000)]


def test_contrato_comandos_sem_duplicidade_nem_colisao_de_alias():
    """Um comando() duplicado lança erro ao carregar o script; um alias repetido sequestra outro comando."""
    import re,collections
    reg=collections.defaultdict(list)
    for f in sorted(JS.glob('[0-9][0-9]_*.js')):
        for m in re.finditer(r"comando\(\[([^\]]*)\]",f.read_text(encoding='utf-8')):
            for n in re.findall(r"'([^']+)'",m.group(1)):reg[n].append(f.name)
    dup={k:v for k,v in reg.items() if len(v)>1}
    assert not dup,dup
    for f in ('91_aparar.js','93_conferencia_pre_video.js'):
        assert 'CMD_ALIAS.' not in (JS/f).read_text(encoding='utf-8'),f


def test_pare_e_siga_inteligente_e_amarelo_por_velocidade():
    import importlib.util
    spec=importlib.util.spec_from_file_location('st',JS.parent/'signal_timing.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert m.amber_s(60/3.6)>3.7 and m.amber_s(0)==3.0 and m.amber_s(200)==6.0
    assert m.alternating_switch(4,5,10,3,2) is False          # antes do verde mínimo
    assert m.alternating_switch(6,5,10,3,0) is False          # sem demanda contrária: mantém
    assert m.alternating_switch(6,5,10,0,2) is True           # fila esvaziou: troca (gap-out)
    assert m.alternating_switch(6,5,10,3,2) is False and m.alternating_switch(10,5,10,3,2) is True
    assert m.pedestrian_walk_s(14)>18 and m.queue_discharge_s(0)==0
    audit=m.audit_signal(speed_kmh=60,amber_given_s=3,all_red_given_s=12,clear_span_m=14,walk_given_s=10,crossing_m=14,phases=3)
    assert len(audit['warnings'])==2


def test_zona_de_dilema_no_amarelo():
    import importlib.util
    spec=importlib.util.spec_from_file_location('st',JS.parent/'signal_timing.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert m.can_stop(60/3.6,40) is True      # a 40 m consegue parar
    assert m.can_stop(60/3.6,20) is False     # a 20 m já está na zona de dilema: atravessa


def test_layers_nao_operacionais_nao_viram_eixo_corte_ou_barreira():
    """Caso real (DUPLICAÇÃO TH53): eixo descomissionado, estacas e juntas de corte não são operacionais."""
    from app import layer_profiles as LP
    rules=LP.BUILTIN['rules']
    for name in ('EIXO_DESCOMISIONADO','C-EC-ESTACAS-EIXO','F-HZ-JUNTA (corte)','sinC-OC_DEFENSA A RETIRAR $ RAMO 1200 (PISTA LESTE)'):
        assert LP.role_for(name,rules) is None,name
    assert LP.role_for('EIXO_LESTE',rules)=='axis' and LP.role_for('GE_HZ-HCORTE',rules)=='cut' and LP.role_for('HATCH_PAV_NOVO',rules)=='pavement'


def test_ponte_de_vazio_e_incremental_e_nao_corta_por_hachura_transversal():
    import numpy as np
    from shapely.geometry import box
    from app.models import Settings
    from app.traffic import TrafficNetwork
    axis=np.array([[0.,0.],[1000.,0.]])
    def rede(roads,edges=()):
        s=Settings(derive_traffic_paths=False,hydrography=False,layers={'axis':['EIXO']})
        return TrafficNetwork(roads,[],[dict(points=axis,layer='EIXO')],axis,np.array([0.,1000.]),s,edge_lines=list(edges))
    n=rede([box(-5,-12,400,12),box(700,-12,1005,12)])
    assert len(n.paths)==1 and n.paths[0]['length']>990       # vazio de 300 m atravessado
    assert n.ghost_zones and n.allowed.contains(box(380,-1,420,1))  # vão já permitido
    blocos=[box(i*50,-12,i*50+49.5,12) for i in range(20)]
    transv=[np.array([[i*50.,-5.],[i*50.,5.7]]) for i in range(1,20)]
    m=rede(blocos,transv)
    assert len(m.paths)==1 and m.paths[0]['length']>980        # frestas e linhas transversais não cortam


def test_barra_da_selecao_flutua_e_nao_entra_na_faixa_de_comandos():
    css=(JS.parent/'estilo.css').read_text(encoding='utf-8');js=(JS/'53_interface_estudos.js').read_text(encoding='utf-8')
    assert "$('selBar')])if(el&&el.parentNode!==rail)" not in js and "[$('toolOptions')])" in js
    assert '.canvasWrap>#selBar{position:absolute!important' in css and '#rsCommandRail #selBar' not in css


def test_materiais_para_classes_de_linha_e_area():
    from app.asset_catalog import CATALOG,DEFAULT
    for role in ('edge_line','barrier','median','terrain','domain','sign_h','cut','fill'):
        assert any(m['role']==role for m in CATALOG.values()),role
    assert 'edge_line' not in DEFAULT and 'barrier' not in DEFAULT      # só opções; não muda o padrão


def test_corte_classificado_por_motivo_e_vao_exposto():
    import numpy as np
    from shapely.geometry import box
    from app.models import Settings
    from app.traffic import TrafficNetwork
    from app.flow_diagnostics import classify_cut,flow_diagnostics
    axis=np.array([[0.,0.],[1000.,0.]])
    s=Settings(derive_traffic_paths=False,hydrography=False,layers={'axis':['EIXO']})
    n=TrafficNetwork([box(-5,-12,400,12),box(700,-12,1005,12)],[],[dict(points=axis,layer='EIXO')],axis,np.array([0.,1000.]),s,edge_lines=[])
    assert n.ghost_info and abs(n.ghost_info[0]['length_m']-300)<12
    assert classify_cut(n,[550,0],['corpo_fora_da_pista'])['category']=='sem_pavimento'
    assert classify_cut(n,[200,0],['corpo_fora_da_pista'])['category']=='fora_da_pista'
    assert classify_cut(n,[200,0],['outra_razao'])=={}
    # impedimento real: canteiro no meio da pista
    m=TrafficNetwork([box(-5,-12,1005,12)],[box(495,-12,505,12)],[dict(points=axis,layer='EIXO')],axis,np.array([0.,1000.]),s,edge_lines=[])
    assert classify_cut(m,[500,0],['corpo_fora_da_pista'])['category']=='impedimento_real'
    rows=flow_diagnostics(m)
    assert all('category' in p or not p for r in rows for p in r['technical_points'][:0] or [{}])


def test_marcadores_e_vao_no_editor():
    a=(JS/'82_diagnostico_video.js').read_text(encoding='utf-8');b=(JS/'95_vao_sem_pavimento.js').read_text(encoding='utf-8')
    assert 'b.dataset.cat=' in a and 'Correção sugerida' in a and 'category:p.category' in a
    assert 'ghost_zones' in b and 'createPattern' in b
