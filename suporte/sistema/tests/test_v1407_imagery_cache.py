from pathlib import Path
import json, os

def _mods(monkeypatch,tmp_path):
    from app import store
    monkeypatch.setattr(store,'ROOT',tmp_path)
    from app import imagery_cache
    return store,imagery_cache

def test_cache_reuses_same_source_without_second_conversion(monkeypatch,tmp_path):
    store,ic=_mods(monkeypatch,tmp_path)
    src=tmp_path/'a.ecw';src.write_bytes(b'ECW-SAMPLE-DATA'*500)
    converted=tmp_path/'a.tif';converted.write_bytes(b'TIFF-CONVERTED'*700)
    entry=ic.register(src,converted,extra={'format':'GeoTIFF'})
    key,hit=ic.lookup(src)
    assert key==entry['key'] and hit is not None
    p1=tmp_path/'p1';p2=tmp_path/'p2'
    d1,linked1=ic.materialize(hit,p1,'imagem_convertido.tif')
    d2,linked2=ic.materialize(hit,p2,'imagem_convertido.tif')
    assert d1.read_bytes()==converted.read_bytes()==d2.read_bytes()
    assert (tmp_path/'_base_imagens').is_dir()
    if linked1 and linked2:
        assert os.stat(d1).st_ino==os.stat(d2).st_ino==os.stat(hit['tif']).st_ino

def test_base_persistente_nao_e_cache_regeneravel(monkeypatch,tmp_path):
    store,ic=_mods(monkeypatch,tmp_path)
    base=ic.base_root()/'aa'/'key';base.mkdir(parents=True);(base/'imagem.tif').write_bytes(b'x')
    pr=tmp_path/('a'*32);(pr/'imagery').mkdir(parents=True);(pr/'imagery'/'x.png').write_bytes(b'x')
    from app import maintenance
    cats={x['id']:x for x in maintenance.survey(tmp_path)}
    assert cats['base_imagens']['padrao'] is False
    assert cats['base_imagens']['bytes']>=1
    maintenance.clean_categories(tmp_path,['caches'])
    assert (base/'imagem.tif').exists()

def test_temporarios_de_sessao_sao_descartados(monkeypatch,tmp_path):
    store,ic=_mods(monkeypatch,tmp_path)
    monkeypatch.delenv('RODOVIA_SESSION_ID',raising=False)
    session=ic.session_temp();(session/'work.bin').write_bytes(b'123')
    assert session.exists()
    ic.cleanup_session()
    assert not session.exists()

def test_residuo_de_sessao_anterior_limpo_na_abertura(monkeypatch,tmp_path):
    store,ic=_mods(monkeypatch,tmp_path)
    old=ic.temp_root()/'old_session';old.mkdir();(old/'x.tmp').write_text('x')
    monkeypatch.setenv('RODOVIA_SESSION_ID','current')
    cur=ic.temp_root()/'current';cur.mkdir()
    removed=ic.prune_orphan_temps(0)
    assert 'old_session' in removed and not old.exists() and cur.exists()

def test_limpeza_inclui_cache_local_web_e_pedido_de_conversao(monkeypatch,tmp_path):
    store,ic=_mods(monkeypatch,tmp_path)
    from app import maintenance
    pr=tmp_path/('b'*32);(pr/'cache_local_web'/'x').mkdir(parents=True);(pr/'cache_local_web'/'x'/'tile.png').write_bytes(b'abc')
    (pr/'imagem_local').mkdir();(pr/'imagem_local'/'_converter.json').write_text('{}',encoding='utf-8')
    cats={x['id']:x for x in maintenance.survey(tmp_path)}
    assert cats['caches']['bytes']>=3 and cats['temporarios']['itens']>=1
    maintenance.clean_categories(tmp_path,['caches','temporarios'])
    assert not (pr/'cache_local_web').exists()
    assert not (pr/'imagem_local'/'_converter.json').exists()
