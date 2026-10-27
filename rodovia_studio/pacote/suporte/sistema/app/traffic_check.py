"""Prévia de conferência curta, separada dos resultados e configurações finais."""
import json,time
from pathlib import Path
from PIL import Image
from .project_state import revision,read_config
from .dependencies import digest,revisions
from . import store
from .render import Scene
from .fleet_compatibility import compatibility

def run(directory,settings,status=lambda *a:None,cancel=lambda:False):
    d=Path(directory);key=digest([revision(settings.model_dump()),revisions(d,settings)]);duration=min(10.,settings.duration_s)
    local=settings.model_copy(update={'duration_s':duration,'camera_mode':'obras'})
    started=time.monotonic();scene=Scene(d,local,status);simulation=scene.traffic(lambda p,m:status(.25+.25*p,m))
    audit=compatibility(simulation,scene.network,local,cancel,lambda p,m:status(.5+.3*p,m))
    end=max(0.,duration-1/settings.fps);samples=[0.,duration/2,end]
    counts=[{'time_s':t,'active':len(list(scene.traffic_iter(t))) if settings.traffic else 0} for t in samples]
    if cancel():raise InterruptedError('Conferência cancelada.')
    if simulation is not None and any(c['active'] for c in counts):scene.s.camera_mode='trafego'
    t=max(counts,key=lambda c:c['active'])['time_s'];image,meta=scene.frame(t,overview=scene.s.camera_mode!='trafego')
    if digest([revision(read_config(d)),revisions(d)])!=key:raise ValueError('O projeto mudou. Refaça a conferência; o resultado antigo não foi aplicado.')
    result={'config_revision':key,'seconds':round(time.monotonic()-started,3),'duration_s':duration,'itineraries':len(scene.network.paths),'samples':counts,'visibility':meta.get('traffic_visibility',{}),'fleet':audit,'source_registration':scene.network.report.get('source_registration',{}),'warnings':scene.network.warnings,'oae':scene.network.oae_report,'scope':'Prévia de conferência de até 10 s; não é o vídeo final, contagem integral ou certificação normativa.'}
    temp=d/'traffic_check.tmp.png';Image.fromarray(image).save(temp);store.replace(temp,d/'traffic_check.png');store.write_json(d/'traffic_check.json',result);status(1,'Conferência pronta; revise causas e compatibilidade por veículo')
    return result
