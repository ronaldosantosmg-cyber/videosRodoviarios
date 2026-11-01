"""Localização PER pela distância real do eixo; não estica km nem move coordenadas manuais."""
import numpy as np
from .chainage import Stationing
from .models import PERWork


def locate_works(settings,axis,works=None,stationing=None):
    points=np.asarray(axis,float)
    if points.ndim!=2 or points.shape[1]!=2 or len(points)<2 or not np.isfinite(points).all():raise ValueError('Eixo inválido para localizar obras.')
    st=stationing or Stationing.from_settings(points,settings)
    if not np.isfinite([st.length,st.scale]).all() or st.length<=.01 or st.scale<=0:raise ValueError('Confira comprimento e calibração do eixo.')
    low,high=map(float,st.km_range());source=settings.works if works is None else works
    if len(source)>1000:raise ValueError('Limite de 1000 obras por projeto.')
    rows=[]
    for i,value in enumerate(source):
        w=value if isinstance(value,PERWork) else PERWork.model_validate(value)
        row={'index':i,'id':w.id,'description':w.description,'point':None,'start_point':None,'end_point':None,'km_start_m':w.km_start_m,'km_end_m':w.km_end_m}
        if w.x is not None:
            point=[float(w.x),float(w.y)];distance=float(st.offset(point)[0]);a=b=float(st.km(point)) if w.km_mode=='auto' and settings.chainage.mode!='off' else None
            row.update(status='coordinates',point=point,start_point=point,end_point=point,offset_m=round(distance,2),message='Coordenadas cadastradas preservadas.'+(' Ponto a mais de 30 m do eixo principal; confira a referência.' if distance>30 else ''))
            if a is not None:row.update(km_start_m=a,km_end_m=b)
        elif settings.chainage.mode=='off':row.update(status='unconfigured',message='Defina o estaqueamento para localizar automaticamente por km.')
        elif w.km_end_m<low-1e-6 or w.km_start_m>high+1e-6:row.update(status='outside',message='Obra fora do intervalo real do eixo; não é deslocada para uma ponta.')
        else:
            a=max(low,float(w.km_start_m));b=min(high,float(w.km_end_m));partial=a>w.km_start_m+1e-6 or b<w.km_end_m-1e-6
            row.update(status='partial' if partial else 'located',point=st.point((a+b)/2).tolist(),start_point=st.point(a).tolist(),end_point=st.point(b).tolist(),visible_km_start_m=a,visible_km_end_m=b,message='Trecho parcialmente abrangido pelo eixo; km originais preservados.' if partial else 'Localizada pelo estaqueamento do eixo.')
        rows.append(row)
    counts={key:sum(r['status']==key for r in rows) for key in ('located','partial','coordinates','outside','unconfigured')}
    return {'rows':rows,'counts':counts,'axis_km_start_m':low,'axis_km_end_m':high,'stationing':st.info(),'scope':'Prévia de localização; não altera a planilha, configurações ou marcos de km.'}
