// Perfil explícito de apresentação: preserva geometria, seções e parâmetros de cálculo.
(()=>{'use strict';
checks.push('natural_materials_only');
queueMicrotask(()=>{
 const anchor=$('texture_style');if(!anchor)return;
 const button=document.createElement('button');button.id='rsArtisticPreset';button.type='button';button.textContent='Aplicar maquete artística natural';
 button.title='Materiais naturais, taludes em solo/vegetação e texturas artísticas. Preserva o projeto e as regras de tráfego.';
 button.onclick=()=>{for(const [id,value] of Object.entries({style_profile:'padrao',texture_style:'artistico',earthwork_look:'natural',visual_quality:'enhanced'}))if($(id))$(id).value=value;
  $('natural_materials_only').checked=true;$('detail_textures').checked=true;$('median_grass').checked=true;
  scheduleSave();msg('Maquete artística natural aplicada. Salve e gere a prévia; as hachuras técnicas permanecem disponíveis no projeto.');
 };
 const label=document.createElement('label');label.innerHTML='<input id="natural_materials_only" type="checkbox"> Usar materiais naturais na maquete (preservar hachuras técnicas no projeto)';label.querySelector('input').onchange=()=>scheduleSave();
 const section=anchor.closest('section'),heading=section?.querySelector(':scope>h2');if(heading){heading.after(button);button.after(label)}else{anchor.parentElement.appendChild(button);button.after(label)}
});
})();
