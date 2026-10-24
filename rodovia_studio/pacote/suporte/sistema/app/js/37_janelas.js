// =====================================================================================================
// 1.32: janelas no padrão do Windows. Cada janela (.winDlg) ganha barra de título com ×, área de conteúdo com
// rolagem e rodapé fixo (a última linha de botões). Só reorganiza os elementos; ids e comportamento não mudam.
// =====================================================================================================
function arrumarJanela(d){if(d.dataset.arrumada)return;d.dataset.arrumada='1';
 let h=d.querySelector(':scope>h3');if(!h){h=document.createElement('h3');h.textContent='Rodovia Studio';d.prepend(h)}
 // O texto do título fica num <span> (com o id do título, se houver): trocar o título não apaga o ×.
 const t=document.createElement('span');t.className='dlgT';while(h.firstChild)t.appendChild(h.firstChild);if(h.id){t.id=h.id;h.removeAttribute('id')}h.appendChild(t);
 const x=document.createElement('button');x.type='button';x.className='dlgX';x.tabIndex=-1;x.title='Fechar (Esc)';x.setAttribute('aria-label','Fechar');x.textContent='×';h.appendChild(x);
 const rows=[...d.querySelectorAll(':scope>.row')];const foot=rows[rows.length-1]||null;
 const body=document.createElement('div');body.className='dlgBody';
 for(const el of [...d.children]){if(el===h||el===foot)continue;body.appendChild(el)}
 if(foot){foot.classList.add('dlgFoot');d.insertBefore(body,foot)}else d.appendChild(body);
 x.addEventListener('click',()=>{
  // Fecha como o “Cancelar/Fechar” da própria janela (as caixas de diálogo que esperam resposta recebem “não”).
  const b=[...d.querySelectorAll('.dlgFoot button')].find(b=>/^(cancelar|fechar|não)/i.test(b.textContent.trim())||/(Cancel|No|Close)$/.test(b.id));
  if(b)b.click();else d.close()})}
document.querySelectorAll('dialog.winDlg').forEach(arrumarJanela);
// A mini-barra da seleção some ao trocar para outra ferramenta (não fica por cima das opções da ferramenta).
estender('setTool',anterior=>function(t){anterior(t);try{placeSelBar()}catch{}},'janelas: mini-barra acompanha a ferramenta');
