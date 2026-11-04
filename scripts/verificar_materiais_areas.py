"""Exercita o Canvas real: material local, automático, textura própria e vazios."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE','/usr/bin/chromium'),args=['--no-sandbox'])
    page=browser.new_page();page.set_content('<canvas id="surface" width="90" height="90"></canvas>')
    page.evaluate('''() => {window.geo={R0:1,k:1};window.view={s:1,ox:0,oy:0};window.worldToImg=p=>[p.x,p.y];window.vecAlpha=1;window.cfg={};window.appearance={texture_style:'artistico',style_profile:'padrao',pavement_material:'rigido',existing_material:'flexivel',tp:{},ps:{}};window.RodoviaAparencia={leitura:()=>window.appearance}}''')
    page.add_script_tag(path=str(root/'suporte/sistema/app/js/94_texturas_vivas.js'))
    result=page.evaluate('''() => {const c=document.getElementById('surface').getContext('2d');const ring=[[5,5],[85,5],[85,85],[5,85]].map(([x,y])=>({x,y}));const hole=[[30,30],[60,30],[60,60],[30,60]].map(([x,y])=>({x,y}));
    const render=(material,texture=null)=>{c.fillStyle='#f00000';c.fillRect(0,0,90,90);const ok=RodoviaTexturasVivas.pintarArea(c,{points:ring,holes:[hole],kind:'pavement',material,texture});const px=[...c.getImageData(15,15,1,1).data],gap=[...c.getImageData(45,45,1,1).data];return {ok,px,gap}};
    return {auto:render('auto'),asphalt:render('flexivel'),concrete:render('rigido'),custom:render('flexivel',{tom:.45,grao:0,remendos:0,fissuras:0})}}''')
    assert all(x['ok'] for x in result.values()),result
    assert result['auto']['px']==result['concrete']['px'],result
    assert sum(result['concrete']['px'][:3])>sum(result['asphalt']['px'][:3])+200,result
    assert result['custom']['px']!=result['asphalt']['px'],result
    assert all(x['gap']==[240,0,0,255] for x in result.values()),result
    page.evaluate("window.vec={layers:{pavement:[{p:[[0,0],[20,0],[20,20],[0,20]],c:true,material:'rigido',existing:false},{p:[[30,0],[50,0],[50,20],[30,20]],c:true,material:'flexivel',existing:false}]}};window.vecPaths={};window.vecOn={};window.VSTYLE={pavement:['#333']};window.buildSignage=()=>{};")
    source=(root/'suporte/sistema/app/js/02_vista_imagem_web.js').read_text()
    function=source[source.index('function buildVectorPaths()'):source.index('function buildSignage()')]
    groups=page.evaluate("() => {"+function+";buildVectorPaths();return vecPaths.pavement.phases.map(p=>({material:p.material,n:p.n}));}")
    assert sorted((g['material'],g['n']) for g in groups)==[('flexivel',1),('rigido',1)],groups
    browser.close()
print('Canvas: material por área, padrão do projeto, textura própria, vazios e materiais distintos no mesmo layer preservados.')
