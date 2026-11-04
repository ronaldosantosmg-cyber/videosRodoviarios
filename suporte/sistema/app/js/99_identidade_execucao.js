// Identidade real da sessão; não muda regras de tráfego nem encerra tarefas.
(()=>{'use strict';
 function label(h){
  const r=h.runtime,version=r?.version_at_start||h.version||'?';
  if(!r)return 'v'+version+' · código ativo não identificado; confira a instalação';
  if(r.disk_changed!==false||r.version_changed_since_import)return 'v'+version+' em execução · arquivos alterados ou indisponíveis; confira e reinicie';
  if(!r.policy?.probe?.ok)return 'v'+version+' · política antiga/incompatível; repare a instalação';
  return 'v'+version+' · política de exportação conferida';
 }
 function status(h){const r=h.runtime,ready=r&&r.disk_changed===false&&!r.version_changed_since_import&&r.policy?.probe?.ok;return (ready?'Ambiente pronto':'Verificar instalação')+' · '+(h.ffmpeg?'FFmpeg disponível':'FFmpeg indisponível')+' · '+label(h)}
 async function open(){
  const existing=document.getElementById('rsRuntimeIdentity');if(existing){existing.focus();return}
  const h=await api('/api/health'),d=document.createElement('dialog');d.id='rsRuntimeIdentity';d.className='winDlg rsModelDialog';
  const header=document.createElement('header'),title=document.createElement('h2'),section=document.createElement('section'),footer=document.createElement('footer'),close=document.createElement('button'),note=document.createElement('p'),pre=document.createElement('pre');
  title.textContent='Diagnóstico da instalação em execução';header.append(title);note.textContent=label(h)+'. O número da versão sozinho não comprova os arquivos carregados. Este diagnóstico não altera o projeto.';pre.textContent=JSON.stringify(h.runtime||{version:h.version,runtime:'Sessão antiga sem identidade detalhada.'},null,2);pre.style.whiteSpace='pre-wrap';pre.style.overflowWrap='anywhere';section.append(note,pre);close.type='button';close.textContent='Fechar';footer.append(close);d.append(header,section,footer);document.body.append(d);const finish=()=>{d.close();d.remove()};close.onclick=finish;d.oncancel=e=>{e.preventDefault();finish()};d.showModal();
 }
 window.RodoviaRuntime=Object.freeze({label,status,open});
 comando(['DIAGNOSTICARINSTALACAO'],open,'Mostra a pasta, o processo, o código carregado e a conferência da política de exportação; identifica sessão antiga e arquivos alterados.');
 const refresh=async()=>{const h=await api('/api/health'),node=document.getElementById('health');if(node)node.textContent=status(h)};
 const start=()=>void refresh().catch(e=>{if(window.RodoviaErros)RodoviaErros.avisar('identidade_execucao',e)});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
