/* ---------- 1.8: Como usar e dicas nos campos ---------- */
const HELP={
 projects:'Projetos já criados neste computador. Cada projeto guarda arquivos, configuração, marcações e vídeos na pasta “projetos”.',
 files:'DXF do projeto (obrigatório para pavimento, OAE etc.) e KMZ opcional (eixo e pontos). DWG deve ser salvo como DXF no CAD.',
 name:'Nome do trecho: aparece no cabeçalho do vídeo.',origin:'Cidade/ponto de origem, mostrado no cabeçalho.',destination:'Cidade/ponto de destino, mostrado no cabeçalho.',
 km_start_m:'Km do início do trecho (ex.: 325+850 ou 325,850). No estaqueamento manual, vale no ponto marcado com “Início do km”.',
 km_end_m:'Km do fim do trecho. Use “Usar km final medido” (Marcações do projeto) para preencher pela distância ao longo do eixo.',
 reference_length_m:'Extensão contratual mostrada no rodapé. Pode diferir do comprimento geométrico do desenho.',
 work_year:'Ano/etapa da obra mostrado no rodapé (ex.: Ano 4 do PER).',
 crs:'Sistema de coordenadas projetado do DXF, em metros (ex.: EPSG:31983 = SIRGAS 2000 / UTM 23S). Errado = desenho fora da imagem.',
 units_to_m:'Multiplicador para converter a unidade do DXF em metros: 1 para metros, 0,001 para milímetros.',
 imagery:'Fundo do vídeo: Esri online (baixa e guarda), imagem guardada no pacote, fundo neutro (teste rápido) ou imagem local georreferenciada.',
 reverse_axis:'Inverte início e fim do eixo principal (sentido da câmera e do km automático).',
 coordinates_confirmed:'Confirme depois de conferir na prévia que o desenho está sobre a imagem. É exigido para gerar o vídeo.',
 preview_mode:'Vista geral: todo o trecho. Câmera do vídeo: o quadro no instante escolhido. Vista do editor: detalhe do enquadramento atual.',
 preview_time_s:'Instante do vídeo usado por “Abrir neste instante”.',
 poiTitle:'Nome da intervenção (aparece no cabeçalho na cena de detalhe).',poiKind:'Categoria: define símbolo e representação (passarela e baia são desenhadas).',
 poiSubtitle:'Texto complementar abaixo do nome no cabeçalho.',poiKmMode:'Calculado: km pelo estaqueamento a partir do ponto X/Y. Manual: km oficial digitado.',
 poiKm:'Km oficial da intervenção (usado quando o modo é Manual).',poiX:'Coordenada X (Este) no CRS do projeto. Use a ferramenta Intervenção para preencher.',poiY:'Coordenada Y (Norte) no CRS do projeto.',
 encoder:'Automática: testa a NVIDIA (NVENC) e usa a CPU se falhar. Somente CPU: mais compatível.',
 cpu_preset:'veryfast: mais rápido; fast: original, um pouco mais eficiente em tamanho.',
 width:'Resolução do vídeo. 720p é bom para testes; 1440p para a versão final; 4K (3840) para telões (bem mais lento e arquivo maior).',video_quality:'Padrão: qualidade básica, com menor custo de geração. Alta: imagem de fundo mais nítida, veículos sem serrilhado e menos compressão (recomendado). Máxima: além disso monta cada quadro 1,5× maior e reduz (bordas e textos lisos), detalhe a 0,1 m e imagem Esri nível 20 onde houver — cerca de 2,5× mais lento.',fps:'Quadros por segundo (30 é mais fluido).',
 duration_s:'Duração do vídeo. Abaixo de 45 s, o modo curto usa vista estável (ver opção abaixo).',
 view_width_m:'Largura do terreno mostrada pela câmera durante o percurso (menor = mais perto).',
 imagery_pixels:'Resolução do mosaico de imagem. 8192 = mais nítido, mais memória e tempo.',
 render_workers:'Quantos processos montam quadros ao mesmo tempo. Automático usa os núcleos e a memória livres do seu PC.',
 render_profile:'Rápido: sem superamostragem da imagem aérea — bom para conferir antes do vídeo final.',
 visual_quality:'Aprimorada: asfalto com textura em metros, concreto nas OAE e veículos por tipo. Anterior: desenho da 1.4, mais rápido.',
 hydrography:'Rios e lagos de bases públicas (IBGE/OSM), com cache local.',water_texture:'Textura azul só dentro dos polígonos de água existentes.',
 water_names:'Nomes dos rios sobre o mapa.',water_animated:'Ondulação sutil animada na água (custa tempo de geração).',headlights:'Faróis acesos com feixe discreto em todos os veículos.',
 traffic:'Veículos em trajetórias validadas (ilustrativo, sem simulação de tráfego).',traffic_speed_kmh:'Velocidade dos veículos ilustrativos.',
 short_video_mode:'Para vídeos curtos: vista estável com aparecimento suave, ou o sobrevoo completo comprimido.',
 traffic_network_preview:'Desenha as trajetórias validadas na imagem da prévia.',
 cabinEnabled:'Gera o vídeo em primeira pessoa a partir do ponto escolhido com a ferramenta Cabine.',
 elSource:'Elevação do terreno: MDT local (GeoTIFF) ou web (~30 m). A imagem aérea não é deformada.',
 elHill:'Sombreamento do relevo sobre a imagem (só brilho; nada muda de lugar).',elCont:'Curvas de nível sobre a imagem, com o intervalo escolhido.',
 elLevel:'A pista segue o perfil suavizado do terreno sob o eixo (aproximação sem greide de projeto).',
 alignMode:'Translação: só desloca. Similaridade: desloca, gira e ajusta a escala (2 pares ou mais).',
 pngRgba:'Também salva cada quadro com fundo transparente para editores de vídeo.',
 overlayFile:'DXF extra sobreposto ao projeto (outro lote, interferências, cadastro). Não altera o DXF principal.',
 baseMode:'Imagem web: ladrilhos Esri World Imagery nítidos em qualquer zoom (guardados em cache para uso sem internet) com o DXF/KMZ simplificado por cima — use para posicionar marcações e pares de controle. Prévia renderizada: a imagem do vídeo. As marcações são as mesmas nos dois fundos (coordenadas do CRS).',
 tileAlpha:'Transparência da imagem web.',vecAlpha:'Transparência dos vetores do DXF/KMZ.',
 signage_style:'Limpa: remove pinturas que se cruzam, sobras de ramos curtos e marcas junto às junções. Anterior: como na 1.9.',flow_arrows:'Setas de sentido do tráfego: uma a cada km (espaçamento abaixo) e antes/depois de convergências, divergências e rotatórias.',flow_arrow_spacing_m:'Distância entre setas ao longo das vias principais.',cities_radius_km:'Distância máxima das cidades buscadas e das setas de borda.',
 km_markers:'Marcadores com o km inicial e o km final sobre o traçado.',direction_badge:'Seta no topo do vídeo indicando para onde o km cresce na posição da câmera.',median_grass:'Textura de grama nos canteiros (qualidade Aprimorada).',cities_show:'Nomes das cidades marcadas; fora do quadro aparece uma seta na borda com a distância.',
 imagery_detail:'Perto do chão, usa a imagem Esri de ~0,3 m (baixada antes da montagem e guardada). Desligada: só o mosaico da vista geral.',detail_textures:'Pavimento, canteiro, taludes e OAE desenhados a 0,2 m por pixel quando a câmera se aproxima (bordas e hachuras nítidas). Aumenta o tempo por quadro.',
 traffic_model:'Simulado: os veículos mantêm distância segura (sem batidas traseiras), cedem passagem nas convergências e formam fila em interdições e engarrafamentos. Anterior: movimento clássico.',traffic_density:'Demanda relativa de veículos: 1 normal; acima de 3 aumenta a pressão sobre a capacidade.',traffic_capacity_vphpl:'Capacidade nominal por faixa, em veículos por hora. Caminhões, ônibus e carretas consomem mais capacidade equivalente.',queue_capacity_model:'Quando ligado, a entrada de veículos respeita a capacidade da faixa: a fila cresce quando a demanda supera a descarga e diminui quando há folga.',heavy_vehicle_reaction:'Carros e demais veículos leves aumentam o headway atrás de pesados; pesados têm aceleração mais lenta e podem gerar pelotões/filas.',median_crossing:'Onde os veículos podem passar de uma pista para a outra do canteiro central.',
 day_night:'Transição: o vídeo começa de dia e escurece no instante escolhido, com faróis, lanternas e sinalização refletiva em destaque. Noite: o vídeo todo à noite.',night_start_s:'Instante do vídeo em que começa a anoitecer.',night_transition_s:'Duração do anoitecer.',night_darkness:'Quanto a cena escurece (0,3 = entardecer; 0,95 = noite fechada).',night_signage_glow:'Faixas e setas brilham como tinta refletiva iluminada pelos faróis.',
 imgFiles:'GeoTIFF, ou JPG/PNG com o arquivo de mundo (.jgw/.pgw/.tfw) e o .prj. Arquivos sem georreferência são recusados.'};
function initHelp(){for(const [id,text] of Object.entries(HELP)){const el=$(id);if(!el)continue;const lab=el.closest('label');const host=lab||el.parentElement;if(!host||host.querySelector(':scope > .help'))continue;
 const b=document.createElement('span');b.className='help';b.tabIndex=0;b.textContent='?';b.dataset.help=text;b.setAttribute('aria-label','Ajuda: '+text);
 if(lab){const firstInput=lab.querySelector('input,select,textarea');if(firstInput&&firstInput.type==='checkbox')lab.appendChild(b);else lab.insertBefore(b,firstInput)}else host.appendChild(b)}
 const tip=$('tip');const show=e=>{const t=e.target.closest('.help');if(!t)return;tip.textContent=t.dataset.help;tip.hidden=false;const r=t.getBoundingClientRect();tip.style.left=Math.min(window.innerWidth-380,Math.max(8,r.left-10))+'px';tip.style.top=(r.bottom+8+tip.offsetHeight>window.innerHeight?r.top-tip.offsetHeight-8:r.bottom+8)+'px'};
 document.addEventListener('mouseover',show);document.addEventListener('focusin',show);document.addEventListener('mouseout',e=>{if(e.target.closest('.help'))tip.hidden=true});document.addEventListener('focusout',e=>{if(e.target.closest('.help'))tip.hidden=true});
 document.addEventListener('click',e=>{if(e.target.closest('.help'))e.preventDefault()},true);
 let on=true;try{on=localStorage.getItem('rodovia_help')!=='0'}catch{}$('helpToggle').checked=on;document.body.classList.toggle('nohelp',!on);
 $('helpToggle').onchange=()=>{document.body.classList.toggle('nohelp',!$('helpToggle').checked);try{localStorage.setItem('rodovia_help',$('helpToggle').checked?'1':'0')}catch{}}}
$('helpBtn').onclick=guard(async()=>{if(!$('helpBody').innerHTML){const r=await fetch('/ajuda');$('helpBody').innerHTML=await r.text()}$('helpDialog').showModal()});
initHelp();

