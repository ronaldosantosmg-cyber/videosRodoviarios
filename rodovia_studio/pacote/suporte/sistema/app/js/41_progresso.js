// =====================================================================================================
// 1.34: progresso sempre visível. Durante qualquer tarefa (análise, prévia, vídeo, exportação) e em todo arquivo
// baixado (registros, prompt para IA, vídeos, exportações), um quadro de progresso aparece no canto inferior
// direito — o que está sendo feito, a barra, a porcentagem, o tempo e Cancelar — além do rodapé.
// =====================================================================================================
const TAREFA_NOME={render:'Gerando vídeo',preview:'Gerando prévia',analyze:'Analisando arquivos',export:'Exportando',frames:'Exportando quadros PNG',
 reference:'Exportando vídeo de referência',compare:'Comparando vídeos',convert_imagery:'Convertendo imagem',install_ecw:'Instalando leitor ECW',reference_profile:'Medindo vídeo',reference_profile_remove:'Medindo vídeo'};
let progCard=null,progAtual=null;
function progQuadro(){if(progCard)return progCard;document.body.insertAdjacentHTML('beforeend','<div id="progCard" class="progCard" hidden role="status" aria-live="polite"><div class="pcTop"><b id="pcTitulo"></b><span class="grow"></span><span id="pcPct" class="pcPct"></span><button type="button" id="pcMin" title="Esconder este quadro (o progresso continua no rodapé)">–</button></div><div class="pcBar"><i id="pcFill"></i></div><div id="pcInfo" class="pcInfo"></div><div class="pcRow"><span id="pcTempo" class="pcTempo"></span><span class="grow"></span><button type="button" id="pcCancel" class="danger">Cancelar</button></div></div>');
 progCard=$('progCard');$('pcMin').onclick=()=>{progCard.hidden=true;if(progAtual)progAtual.escondido=true};$('pcCancel').onclick=()=>{progAtual?.cancelar?.()};return progCard}
// estado: {titulo, valor 0–1 ou null (indeterminado), info, inicio, cancelar}
function progMostrar(st){progQuadro();progAtual={inicio:Date.now(),...progAtual&&progAtual.id===st.id?progAtual:{},...st};const p=progAtual;
 if(!p.escondido)progCard.hidden=false;$('pcTitulo').textContent=p.titulo||'Processando';
 const v=p.valor==null?null:Math.max(0,Math.min(1,p.valor));progCard.classList.toggle('indet',v==null);$('pcFill').style.width=v==null?'30%':(v*100).toFixed(1)+'%';$('pcPct').textContent=v==null?'':Math.round(v*100)+'%';
 $('pcInfo').textContent=tempoTexto(p.info||'');const el=(Date.now()-p.inicio)/1000,rest=v>.03?el*(1-v)/v:null;$('pcTempo').textContent=`${tempo(el)}${rest!=null&&v<1?` · falta ~${tempo(rest)}`:''}`;
 $('pcCancel').hidden=!p.cancelar}
function progFim(id,texto,erro){if(!progAtual||progAtual.id!==id)return;const card=progQuadro();
 if(texto){$('pcInfo').textContent=texto;$('pcFill').style.width='100%';card.classList.remove('indet');card.classList.toggle('erro',!!erro);$('pcCancel').hidden=true}
 const fim=progAtual;setTimeout(()=>{if(progAtual===fim){card.hidden=true;card.classList.remove('erro');progAtual=null}},texto?2500:0)}
// Tarefas do servidor: o quadro acompanha o progresso e a mensagem enquanto a tarefa roda.
estender('poll',anterior=>async function(jid){let kind='';try{kind=(await api('/api/jobs/'+jid)).kind||''}catch{}
 const id='job:'+jid;progMostrar({id,titulo:TAREFA_NOME[kind]||'Processando',valor:0,info:'',cancelar:()=>$('cancel')?.click()});
 const t=setInterval(()=>{if(progAtual?.id===id)progMostrar({id,valor:Number($('progress').value)||0,info:$('message').textContent})},700);
 let r,estado='';try{r=await anterior(jid);try{estado=(await api('/api/jobs/'+jid)).state}catch{}}finally{clearInterval(t)}
 progFim(id,estado==='done'?'Concluído.':estado==='cancelled'?'Cancelado.':estado==='failed'?'Falhou — veja a mensagem no rodapé.':'',estado==='failed');return r},'progresso: quadro durante a tarefa');
// Arquivos baixados: lidos em partes para mostrar o progresso; depois salvos com o nome do servidor.
function nomeDoArquivo(resp,url){const cd=resp.headers.get('content-disposition')||'';const m=/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(cd);
 if(m)return decodeURIComponent(m[1]||m[2]);try{return decodeURIComponent(new URL(url,location.href).pathname.split('/').pop())||'arquivo'}catch{return 'arquivo'}}
async function baixarArquivo(url,titulo){const id='dl:'+url+Date.now();const ctl=new AbortController();
 progMostrar({id,titulo:titulo||'Baixando',valor:null,info:'Preparando o arquivo…',cancelar:()=>ctl.abort()});
 try{const resp=await fetch(url,{signal:ctl.signal});if(!resp.ok){let d='';try{d=(await resp.json()).detail}catch{}throw Error(d||`Não foi possível baixar (${resp.status}).`)}
  const total=Number(resp.headers.get('content-length'))||0,nome=nomeDoArquivo(resp,url);const partes=[];let n=0;
  if(resp.body&&resp.body.getReader){const rd=resp.body.getReader();for(;;){const {done,value}=await rd.read();if(done)break;partes.push(value);n+=value.length;
    progMostrar({id,titulo:titulo||'Baixando',valor:total?n/total:null,info:`${nome} · ${MB(n)}${total?' de '+MB(total):''}`})}}
  else{partes.push(new Uint8Array(await resp.arrayBuffer()));n=partes[0].length}
  const blob=new Blob(partes,{type:resp.headers.get('content-type')||'application/octet-stream'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=nome;document.body.appendChild(a);a.click();
  setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},4000);progFim(id,`${nome} (${MB(n)}) salvo na pasta de downloads.`);msg(`Arquivo salvo: ${nome} (${MB(n)}).`);return nome}
 catch(e){if(e.name==='AbortError'){progFim(id,'Download cancelado.');msg('Download cancelado.');return null}progFim(id,e.message,true);msg(e.message,true);return null}}
// Links de download da interface passam pelo baixarArquivo (mesmo destino, agora com progresso).
const DL_RE=/(\.(zip|md|mp4|json|png|csv|dxf|kml|kmz|txt)(\?|$))|[?&]baixar=1/i;
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[href]');if(!a||e.defaultPrevented||e.ctrlKey||e.shiftKey||e.metaKey||e.button)return;
 const h=a.getAttribute('href')||'';if(!h.startsWith('/api/')||!DL_RE.test(h))return;e.preventDefault();baixarArquivo(h,a.dataset.titulo||'Baixando '+(a.textContent||'').trim().replace(/^[⭳\s]+/,''))});
function baixarRegistros(){if(!pid)return msg('Abra um projeto primeiro.',true);return baixarArquivo(`/api/projects/${pid}/registros.zip`,'Baixando registros')}
function promptIA(){if(!pid)return msg('Abra um projeto primeiro.',true);return baixarArquivo(`/api/projects/${pid}/prompt_ia.md`,'Exportando prompt para IA')}
