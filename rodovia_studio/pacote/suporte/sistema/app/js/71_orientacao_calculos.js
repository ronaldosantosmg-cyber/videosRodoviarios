// Sistema especialista local para falhas de cálculo; não abre janelas durante o motor.
(()=>{'use strict';
let latest=null,generation=0,dialog=null;
const originalApi=api;
async function advise(kind,message,point=null){
 const stamp=++generation,project=pid;
 try{const data=await originalApi('/api/calculations/guidance',json('POST',{kind:String(kind).slice(0,80),message:String(message||'').slice(0,8000),point}));if(stamp!==generation||project!==pid)return;latest={...data,project};const b=$('rsCalculationGuide');if(b){b.textContent='Orientação: corrigir cálculo…';b.classList.add('on');b.title='Ver causas possíveis e passos de correção do último cálculo.'}return data}catch{return null}
}
const previousStart=start;start=async function(kind,...args){try{return await previousStart(kind,...args)}catch(error){void advise(kind,error.message,kind==='analyze'?segById(selSeg?.id)?.technical_points?.[0]?.point:null);throw error}};
api=async function(url,...args){try{const data=await originalApi(url,...args);if(/\/api\/jobs\//.test(String(url))&&data?.state==='failed')void advise(data.kind||'cálculo',data.message||data.error);return data}catch(error){if(/alignment\/fit|flow-tools|scene3d|convert_imagery|avanco|image_context/.test(String(url)))void advise(String(url).split('/').slice(-2).join(' · '),error.message);throw error}};
function show(){
 if(dialog?.open)return;
 const d=document.createElement('dialog');dialog=d;d.className='winDlg';d.style.padding='18px 22px';d.style.maxHeight='80vh';d.style.overflow='auto';
 const h=document.createElement('h3');h.textContent='Orientação dos cálculos';d.appendChild(h);
 const intro=document.createElement('p');intro.textContent='Sistema especialista local de regras. Não envia dados a uma IA externa nem executa correções automaticamente.';d.appendChild(intro);
 const choices=document.createElement('select');choices.setAttribute('aria-label','Função de cálculo');for(const [value,label] of [['analyze','Análise de fluxos'],['preview','Prévia'],['render','Vídeo'],['scene3d','Cena 3D'],['convert_imagery','Conversão de imagem'],['alignment','Alinhamento']]){const o=document.createElement('option');o.value=value;o.textContent=label;choices.appendChild(o)}d.appendChild(choices);const explain=document.createElement('button');explain.textContent='Orientações desta função';explain.onclick=guard(async()=>{const data=await advise(choices.value,'');if(data){d.close();d.remove();dialog=null;show()}});d.appendChild(explain);
 const data=latest?.project===pid?latest:null;
 if(data){const title=document.createElement('h4');title.textContent=data.title;d.appendChild(title);const causes=document.createElement('p');causes.textContent='Possíveis causas: '+data.causes.join(' · ');d.appendChild(causes);const list=document.createElement('ol');for(const text of data.steps){const li=document.createElement('li');li.textContent=text;list.appendChild(li)}d.appendChild(list);const original=document.createElement('details'),summary=document.createElement('summary'),msg=document.createElement('p');summary.textContent='Mensagem original do cálculo';msg.textContent=data.message;original.append(summary,msg);d.appendChild(original);if(data.point){const locate=document.createElement('button');locate.textContent='Localizar ponto problemático';locate.onclick=guard(async()=>{d.close();d.remove();dialog=null;if(window.RodoviaPanels&&!await RodoviaPanels.close())return;if(!ready())throw Error('Abra a vista do projeto para localizar o ponto.');setTool('pan');zoomTo(P(data.point));draw()});d.appendChild(locate)}}else{const p=document.createElement('p');p.textContent='Nenhuma falha de cálculo registrada nesta sessão. Ao falhar análise, prévia, vídeo, 3D, conversão ou alinhamento, este botão mostrará orientações. Para trajetórias, use Corrigir fluxos.';d.appendChild(p)}
 const repair=document.createElement('button');repair.textContent='Como corrigir este fluxo';repair.onclick=guard(async()=>{d.close();d.remove();dialog=null;await RodoviaFlowRepair.open()});d.appendChild(repair);
 const close=document.createElement('button');close.textContent='Fechar';close.onclick=()=>{d.close();d.remove();dialog=null};d.appendChild(close);d.addEventListener('cancel',()=>{d.remove();dialog=null});document.body.appendChild(d);d.showModal();
}
queueMicrotask(()=>queueMicrotask(()=>{const b=document.createElement('button');b.type='button';b.id='rsCalculationGuide';b.textContent='Orientação dos cálculos';b.onclick=show;if($('rsRepairFlows'))$('rsRepairFlows').after(b);else $('rsTechnicalOptions')?.prepend(b)}));
window.addEventListener('rodovia:project-state',()=>{if(latest?.project!==pid){latest=null;generation++;const b=$('rsCalculationGuide');if(b){b.textContent='Orientação dos cálculos';b.classList.remove('on')}}});
window.RodoviaCalculationGuide=Object.freeze({advise,open:show});
})();
