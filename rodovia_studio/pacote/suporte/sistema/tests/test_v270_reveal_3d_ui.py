"""Compilação real dos shaders e captura WebGL sem antecipar o projeto."""
import base64,io,os
from pathlib import Path
import numpy as np
from PIL import Image
from test_v1425_live_3d import live,gl_page


def test_webgl_capture_reveals_project_and_restores_complete_editing_view(gl_page,live):
    p=gl_page;errors=[]
    p.on('console',lambda m:errors.append(m.text) if m.type=='error' and any(s in m.text for s in ('Shader','GL_INVALID','THREE.WebGLProgram')) else None)
    result=p.evaluate('''async ({url,pid})=>{
      const {RoadViewer}=await import('/webgl/viewer.mjs');const data=await (await fetch(url+'/api/projects/'+pid+'/scene3d.json')).json();
      const div=document.createElement('div');Object.assign(div.style,{position:'fixed',left:'0',top:'0',width:'640px',height:'360px',zIndex:99999});document.body.append(div);
      const viewer=new RoadViewer(div);viewer.load(data);viewer.fit(true);const restore=viewer.captureSize(640,360,data.duration_s);
      const shots=[];for(const time of [0,data.duration_s]){viewer.setTime(time);const blob=await viewer.png();shots.push(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result.split(',')[1]);r.readAsDataURL(blob)}))}
      const during=viewer.reveal.enabled.value;restore();const after=viewer.reveal.enabled.value;viewer.dispose();div.remove();return {shots,during,after};
    }''',{'url':live[0],'pid':live[1]})
    assert result['during']==1 and result['after']==0 and not errors,errors
    images=[Image.open(io.BytesIO(base64.b64decode(b))).convert('RGB') for b in result['shots']]
    assert np.abs(np.asarray(images[0]).astype(float)-np.asarray(images[1])).mean()>1
    out=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs270-artifacts'));out.mkdir(parents=True,exist_ok=True)
    for name,image in zip(('270_3d_inicio','270_3d_final'),images):image.save(out/(name+'.png'))
