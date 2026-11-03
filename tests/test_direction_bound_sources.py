"""A retained CAD alignment still owns its direction after the source DXF changes."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from app.models import Settings, RouteAlignment
from app.native_axes import direction_diagnostics, needs_direction_review
from app.direction_policy import relatorio
from app.central import _chaves_orfas
from app.routes import build_lanes

JS=Path(__file__).resolve().parents[1]/'suporte/sistema/app/js'


def config(enabled=True):
    r=RouteAlignment(id='leste',name='Leste',points=[{'x':0,'y':0},{'x':200,'y':0}],
                     type='unico',enabled=enabled,source_axis_fingerprint='a'*64,source_axis_layer='EIXO_LESTE')
    west=r.model_copy(update={'id':'oeste','name':'Oeste','source_axis_fingerprint':'c'*64,'source_axis_layer':'EIXO_OESTE'})
    return Settings(route_alignments=[r,west],route_directions={'axis:'+'a'*64:'reverse','axis:'+'c'*64:'forward'})


def test_retained_source_is_not_orphan_even_when_temporarily_disabled(tmp_path):
    for enabled in (True,False):
        s=config(enabled)
        assert direction_diagnostics([],s)['orphan_keys']==0
        assert not needs_direction_review([],s)
        assert relatorio([],s)['orfas']==[]
        (tmp_path/'analysis.json').write_text('{"routes":[]}')
        assert _chaves_orfas(tmp_path,s)=={'route_directions':[],'axis_types':[]}
    s=s.model_copy(update={'route_alignments':[]})
    assert direction_diagnostics([],s)['orphan_keys']==2
    assert needs_direction_review([],s)
    assert len(_chaves_orfas(tmp_path,s)['route_directions'])==2


@pytest.mark.skipif(shutil.which('node') is None,reason='Node unavailable')
def test_apply_cleanup_reopen_preserves_the_same_direction():
    s=config();s.route_directions['axis:'+'b'*64]='forward'
    source=(JS/'01_estado_configuracao.js').read_text()
    fluxo=re.search(r'const FLUXO=\(\(\)=>\{.*?\n\}\)\(\);',source,re.S).group(0)
    script='global.document=undefined;global.window=global;global.cfg='+s.model_dump_json()+';'+fluxo
    script+=';global.RodoviaGlossario={opcoes:()=>[]};'+(JS/'94_sentido_eixo.js').read_text()
    script+=';const count=RodoviaSentidoEixo.resumo("EIXO_LESTE").n;const removed=FLUXO.limparOrfas(new Set());console.log(JSON.stringify({count,removed,cfg}));'
    r=subprocess.run(['node','-e',script],capture_output=True,text=True,check=True,timeout=15)
    data=json.loads(r.stdout)
    assert data['count']==1 and data['removed']==1
    restored=Settings.model_validate(data['cfg'])
    assert {p['dir'] for p in build_lanes(restored.route_alignments[0],restored)}=={'r'}
    assert {p['dir'] for p in build_lanes(restored.route_alignments[1],restored)}=={'f'}
    assert restored.route_directions=={'axis:'+'a'*64:'reverse','axis:'+'c'*64:'forward'}
