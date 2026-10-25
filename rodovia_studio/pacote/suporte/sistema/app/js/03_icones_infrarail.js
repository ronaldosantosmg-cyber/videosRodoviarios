// Símbolos locais fornecidos pelo usuário; não acrescentam comandos ou modelos.
(()=>{'use strict';
const tools=Object.freeze({flowcut:'delete-segment',flowjoin:'merge-segments',flowadd:'route-builder',dir:'single-flow',railway:'catenary-rail',traffic_signal:'cantilever-signal',oae:'oae-viaduct',city:'building-facility',veg:'vegetation-tree',light3d:'day-mode'});
const materials=Object.freeze({oae:'oae-viaduct',vegetation:'vegetation-tree',railway:'catenary-rail',gas:'gas-pipeline',electric:'catenary-rail',pole:'power-pole',building:'building-facility',fiber:'fiber-optics',radar:'radar-speed',tower:'transmission-tower',erosion:'slope-erosion',anchored_wall:'tieback-wall',earthwork:'earthwork-gabion',water:'hydrology-river'});
function icon(name){if(!/^[a-z0-9-]+$/.test(name||'')||!document.getElementById('infrarail-'+name))return '';return `<svg class="rsInfraIcon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" aria-hidden="true" focusable="false"><use href="#infrarail-${name}"></use></svg>`}
window.RodoviaInfraRail=Object.freeze({icon,forTool:id=>icon(tools[id]),forMaterial:role=>icon(materials[role])});
})();
