// Parâmetros locais de apresentação e aleatoriedade reprodutível.
(()=>{'use strict';
PROP_LABEL.bridge_clearance_m=['Gabarito da passarela (m)','Altura livre acima do maior nível de via/ferrovia cruzado; mínimo de 5,5 m no modelo ilustrativo.'];
queueMicrotask(()=>{const anchor=$('pedestrians');if(!anchor)return;const box=document.createElement('div');box.className='row';
box.innerHTML='<label><input type="checkbox" id="rail_smoke" checked> Fumaça dos trens</label><label>Semente dos pedestres<input id="pedestrian_seed" type="number" min="0" max="1000000000" value="1729"></label><p class="muted">Travessias são controladas pelo motor; caminhos informais sobre pista/ferrovia não geram pedestres. Semente igual reproduz a mesma sequência.</p>';
anchor.closest('label').after(box);fields.push('pedestrian_seed');numeric.push('pedestrian_seed');checks.push('rail_smoke');
$('rail_smoke').checked=cfg.rail_smoke??true;$('pedestrian_seed').value=cfg.pedestrian_seed??1729;
function readSeed(){const raw=$('pedestrian_seed').value.trim(),value=Number(raw);if(!raw||!Number.isSafeInteger(value)||value<0||value>1000000000)throw Error('Semente dos pedestres: informe um inteiro de 0 a 1.000.000.000.');return value}
const originalCollect=collect;collect=function(...args){readSeed();return originalCollect(...args)};
for(const id of ['rail_smoke','pedestrian_seed'])$(id).addEventListener('change',guard(()=>{readSeed();checkpoint();changed('Parâmetros dos agentes alterados. Recalcule antes de gerar a apresentação.')}));
const prior=fill;fill=function(s,...args){const result=prior(s,...args);$('rail_smoke').checked=s.rail_smoke??true;$('pedestrian_seed').value=s.pedestrian_seed??1729;return result};
});
})();
