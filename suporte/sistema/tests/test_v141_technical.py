from pathlib import Path
import numpy as np
import sys
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))

def test_rollback_api_and_updater_present():
    up=(BASE/'atualizador.py').read_text(encoding='utf-8')
    api=(BASE/'app/rotas/sistema.py').read_text(encoding='utf-8')
    html=(BASE/'app/index.html').read_text(encoding='utf-8')
    assert 'def restore_previous(' in up
    assert '--restaurar-anterior' in up
    assert "'/api/atualizacao/restaurar'" in api
    assert 'updRestore' in html

def test_orthomosaic_module_uses_border_connected_and_fill_holes():
    s=(BASE/'app/orthomosaic.py').read_text(encoding='utf-8')
    assert 'binary_propagation' in s
    assert 'binary_fill_holes' in s
    assert '-crop_to_cutline' in s
    assert '-dstalpha' in s
    assert "'-of','COG'" in s
    assert 'nearblack' in s and "'floodfill'" in s

def test_no_fixed_project_identity_in_new_modules():
    for rel in ['app/orthomosaic.py','atualizador.py']:
        txt=(BASE/rel).read_text(encoding='utf-8').lower()
        assert 'br-381' not in txt and 'br381' not in txt


def test_internal_white_is_preserved_but_border_white_is_removed():
    from app.orthomosaic import _valid_mask_from_rgb
    rgb=np.zeros((3,12,12),dtype=np.uint8)+80
    rgb[:,0,:]=255;rgb[:,-1,:]=255;rgb[:,:,0]=255;rgb[:,:,-1]=255
    rgb[:,5:7,5:7]=255  # telhado/faixa branca interna
    valid,external=_valid_mask_from_rgb(rgb,248,0,1)
    assert not valid[0,0]
    assert external[0,0]
    assert valid[5,5]
    assert not external[5,5]
