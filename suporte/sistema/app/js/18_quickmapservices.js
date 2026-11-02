// ---------------- 1.25: catálogo QuickMapServices ----------------
const qms={items:[],offset:0,next:false,tests:{}};
function qmsFmtArea(r){if(!r.extent)return 'cobertura não informada';const [a,b,c,d]=r.extent;const km=Math.abs(c-a)*111*Math.cos((b+d)/2*Math.PI/180),kn=Math.abs(d-b)*111;return km>2000||kn>2000?'cobertura mundial/continental':`cobertura ~${Math.round(km).toLocaleString('pt-BR')} × ${Math.round(kn).toLocaleString('pt-BR')} km`}
function qmsRender(){const box=$('qmsList');if(!box)return;const cur=cfg?.web_imagery?.qms_id;
 box.innerHTML=qms.items.map(r=>{const t=qms.tests[r.id];const thumb=t&&t.jpeg_b64?`<img alt="amostra" src="data:image/jpeg;base64,${t.jpeg_b64}">`:`<div class="qmsThumb">${t&&t.loading?'testando…':t&&t.usable===false?'não usável':'sem amostra'}</div>`;
  const q=t&&t.usable!==false&&t.nitidez!=null?`<div class="m">Nitidez <b>${t.nitidez.toLocaleString('pt-BR')}</b> · zoom testado ${t.zoom}${t.z_max!=null?' (máx. '+t.z_max+')':''} · falhas ${Math.round(t.vazio*100)}%${t.vazio>0.25?' — <span class="bad">área com falhas ou sem imagem</span>':''}</div>`:'';
  const bad=t&&t.usable===false?`<div class="bad">${esc(t.reason||'')}</div>`:(!r.merc_ok?`<div class="bad">EPSG:${esc(String(r.epsg))} — não usável (só Web Mercator)</div>`:'');
  const warn=t&&t.restricted?'<div class="warn">Provedor com termos restritivos — use só com autorização.</div>':'';
  return `<div class="qmsItem${cur===r.id?' inuse':''}" data-qms="${r.id}">${thumb}<div><div class="t">${esc(r.name)}${cur===r.id?' · <span style="color:#4c8">em uso</span>':''}</div><div class="m">${r.type.toUpperCase()} · ${r.status==='works'?'funcionando':esc(r.status||'situação desconhecida')} · ${qmsFmtArea(r)} · id ${r.id}</div>${q}${bad}${warn}
   <div class="row"><button type="button" data-qa="test">Testar no trecho</button><button type="button" data-qa="use" class="primary"${!r.merc_ok||(t&&t.usable===false)?' disabled':''}>Usar</button><button type="button" data-qa="info">Detalhes e termos</button></div></div></div>`}).join('')||'<p class="muted">Nenhum serviço encontrado com esses filtros.</p>'}
async function qmsSearch(more){if(!pid)throw Error('Abra um projeto.');const off=more?qms.offset+40:0;
 const p=new URLSearchParams({q:$('qmsQ').value.trim(),tipo:$('qmsTipo').value,cobre:$('qmsCobre').checked,funcionando:$('qmsWorks').checked,so_imagem:$('qmsImg').checked,offset:off});
 $('qmsInfo').textContent='Consultando o QuickMapServices…';const r=await api(`/api/projects/${pid}/qms/buscar?${p}`);
 qms.items=more?qms.items.concat(r.results.filter(x=>!qms.items.some(y=>y.id===x.id))):r.results;qms.offset=r.offset;qms.next=r.next;$('qmsMore').hidden=!r.next;
 $('qmsInfo').textContent=`${qms.items.length} serviço(s) listado(s) de ${r.count} no catálogo para esta busca${r.origem!=='online'?' · resultado do '+r.origem:''}. Ordem: imagens aéreas, funcionando e de cobertura local primeiro.`;qmsRender()}
async function qmsTest(id){qms.tests[id]={loading:true};qmsRender();try{qms.tests[id]=await api(`/api/projects/${pid}/qms/${id}/teste`)}catch(e){qms.tests[id]={usable:false,reason:e.message}}qmsRender();return qms.tests[id]}
$('qmsBuscar')?.addEventListener('click',guard(()=>qmsSearch(false)));
$('qmsMore')?.addEventListener('click',guard(()=>qmsSearch(true)));
$('qmsTestTop')?.addEventListener('click',guard(async()=>{if(!qms.items.length)await qmsSearch(false);const L=qms.items.filter(r=>r.merc_ok).slice(0,8);if(!L.length)throw Error('Nenhum serviço usável na lista.');
 $('qmsInfo').textContent=`Testando ${L.length} serviço(s) no centro do trecho…`;for(const r of L)await qmsTest(r.id);
 const sc=r=>{const t=qms.tests[r.id];return !t||t.usable===false||t.nitidez==null?-1:t.nitidez*(1-Math.min(1,t.vazio))};qms.items.sort((a,b)=>sc(b)-sc(a));qmsRender();
 const best=qms.items[0],t=qms.tests[best.id];$('qmsInfo').textContent=t&&t.nitidez!=null?`Mais nítido no trecho: ${best.name} (nitidez ${t.nitidez.toLocaleString('pt-BR')}). Compare as amostras — nitidez alta também pode vir de ruído ou compressão; confira a data da imagem.`:'Nenhum serviço respondeu com imagem no trecho.'}));
$('qmsList')?.addEventListener('click',guard(async e=>{const b=e.target.closest('button[data-qa]');if(!b)return;const id=Number(b.closest('[data-qms]').dataset.qms),a=b.dataset.qa;
 if(a==='test'){const t=await qmsTest(id);if(t.usable===false)msg(t.reason,true);else msg(`Amostra baixada: nitidez ${t.nitidez}, falhas ${Math.round(t.vazio*100)}%.`);return}
 if(a==='info'){const d=await api(`/api/qms/${id}`);const L=[d.name,`Tipo ${String(d.type).toUpperCase()} · EPSG ${d.epsg??'não informado'} · zoom ${d.z_min??'?'}–${d.z_max??'?'}`,d.copyright_text&&'Crédito: '+d.copyright_text,d.license_name&&'Licença: '+d.license_name,(d.terms_url||d.license_url||d.copyright_url)&&'Termos/licença: '+(d.terms_url||d.license_url||d.copyright_url),d.restricted&&'Atenção: provedor com termos restritivos para uso dos ladrilhos fora dos aplicativos dele.',!d.usable&&'Não usável: '+d.reason].filter(Boolean);
  await confirmBox(L.join('\n'),'OK','Fechar');return}
 if(a==='use'){let d=await api(`/api/qms/${id}`);if(!d.usable)throw Error(d.reason);let ok=false;
  if(d.restricted){ok=await confirmBox(`${d.name}: os termos deste provedor costumam proibir baixar os ladrilhos para uso fora dos aplicativos dele (por exemplo, em vídeo). Confirma que a concessionária tem autorização para este uso?`,'Tenho autorização','Cancelar');if(!ok)return}
  const r=await api(`/api/projects/${pid}/qms/${id}/usar`,json('POST',{aceito_termos:ok}));cfg.web_imagery=r.web_imagery;tiles.clear();webUi();qmsRender();draw();
  msg(`Fonte aplicada: ${d.name} (QuickMapServices). O editor já usa a nova imagem; gere a prévia para atualizar o mosaico do vídeo.`)}}));
estender('webUi',_wu=>function(){_wu();const w=cfg?.web_imagery||{};if(w.qms_id&&$('webInfo'))$('webInfo').textContent+=` · catálogo QuickMapServices: ${w.qms_name||('id '+w.qms_id)}`+(w.terms_url?` · termos: ${w.terms_url}`:'')},'1.25: catálogo QuickMapServices');

