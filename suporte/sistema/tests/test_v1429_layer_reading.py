import ezdxf
from app.layer_catalog import catalog
from app.geometry import analyze
from app.models import Settings


def test_reader_retains_named_layers_and_nested_block_inheritance(tmp_path):
    doc=ezdxf.new()
    for name in ('EIXO','PAVIMENTO','CAMADA_VAZIA'):doc.layers.new(name)
    block=doc.blocks.new('TRECHO')
    block.add_line((0,0),(100,0),dxfattribs={'layer':'0'})
    block.add_line((0,2),(100,2),dxfattribs={'layer':'PAVIMENTO'})
    nested=doc.blocks.new('CONJUNTO');nested.add_blockref('TRECHO',(0,0))
    doc.modelspace().add_blockref('CONJUNTO',(0,0),dxfattribs={'layer':'EIXO'})
    doc.saveas(tmp_path/'input.dxf')
    layers={r['name']:r for r in catalog(tmp_path)['layers']}
    assert layers['EIXO']['count']==1
    assert layers['PAVIMENTO']['count']==1
    assert layers['CAMADA_VAZIA']['count']==0
    assert layers['0']['count']==0
    assert catalog(tmp_path)['layers']==list(layers.values())


def test_mapping_original_layer_survives_automatic_color_split(tmp_path):
    doc=ezdxf.new();doc.layers.new('EIXO')
    for i in range(22):doc.modelspace().add_line((i*10,0),((i+1)*10,0),dxfattribs={'layer':'EIXO','color':1+i%2})
    doc.saveas(tmp_path/'input.dxf')
    preview=[]
    result=analyze(tmp_path,Settings(layers={'axis':['EIXO']},layer_split='auto'),preview=preview)
    assert len([e for e in result[0] if e['role']=='axis'])==22
    assert len(result[4]['layers'])==2
    assert not preview, 'Uma camada classificada não deve voltar a aparecer como não mapeada.'
