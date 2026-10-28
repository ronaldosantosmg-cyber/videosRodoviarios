import numpy as np
from test_v139 import montar,amostra,imagem


def test_rgba_border_removed_but_254_and_internal_white_preserved(tmp_path):
    rgb=imagem();a=np.dstack([rgb,np.full(rgb.shape[:2],255,np.uint8)])
    m=montar(tmp_path,a,'borda')
    assert amostra(m,150,600)[:,:,3].max()==0
    assert amostra(m,1200,70)[:,:,3].max()==0
    assert amostra(m,1600,650)[:,:,3].min()==255
    assert amostra(m,320,600,n=40,r=.5)[:,:,3].min()==255


def test_existing_transparency_is_never_restored_and_keep_mode_keeps_white(tmp_path):
    rgb=imagem();a=np.dstack([rgb,np.full(rgb.shape[:2],255,np.uint8)]);a[400:500,1000:1200,3]=0
    m=montar(tmp_path,a,'borda')
    assert amostra(m,1100,450)[:,:,3].max()==0
    m=montar(tmp_path,a,'none')
    assert amostra(m,150,600)[:,:,3].min()==255
    assert amostra(m,1100,450)[:,:,3].max()==0
