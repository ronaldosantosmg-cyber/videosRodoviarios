"""Pacote fornecido: SVG local, identidade por instância e mapeamento sem trocar ações."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path


def test_all_user_icons_are_local_valid_and_match_the_catalog():
    root=Path(__file__).resolve().parents[1]/'app/icons/rodovia';rows=json.loads((root/'catalogo.json').read_text());assert len(rows)==148 and len({r['id'] for r in rows})==148
    for row in rows:
        svg=ET.parse(root/'svg'/row['file_name']).getroot();assert svg.get('viewBox')=='0 0 24 24'
        ids=[]
        for e in svg.iter():
            assert e.tag.rsplit('}',1)[-1] not in ('script','foreignObject','image','animate','set')
            for k,v in e.attrib.items():
                assert not k.rsplit('}',1)[-1].lower().startswith('on') and k.rsplit('}',1)[-1] not in ('href','src','style')
                if 'url(' in v:assert re.fullmatch(r'url\(#[A-Za-z0-9_-]+\)',v)
            if e.get('id'):ids.append(e.get('id'))
        assert len(ids)==len(set(ids))
    assert not list(root.glob('*.html'))
