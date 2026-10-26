"""Contrato único de dependências para o editor e os resultados derivados.

Campos desconhecidos invalidam geometria por segurança. Somente parâmetros
explicitamente classificados deixam de provocar recálculos de trajetórias.
"""
import hashlib,json
from pathlib import Path
from .models import Settings

TRAFFIC=set('route_alignments route_directions direction_marks flow_overrides flow_recoveries flow_cuts min_route_segment_m median_crossing derive_traffic_paths lane_zones lanes_per_direction lane_width_m flow_arrows flow_arrow_spacing_m signage_style signage_detail lane_arrows lane_arrow_repeat arrow_min_gap_m pedestrians pedestrian_paths pedestrian_seed alternating_zones traffic traffic_model traffic_density traffic_capacity_vphpl traffic_demand_vphpl traffic_speed_kmh vehicle_mix queue_capacity_model heavy_vehicle_reaction curve_speed lane_blocks railways traffic_signals signal_links'.split())
SIMULATION=set('traffic traffic_model traffic_density traffic_capacity_vphpl traffic_demand_vphpl traffic_speed_kmh vehicle_mix queue_capacity_model heavy_vehicle_reaction curve_speed'.split())
CAMERA=set('width fps duration_s preview_mode preview_time_s preview_center preview_width_m view_width_m camera_mode camera_path camera_keys short_video_mode cabin render_workers encoder cpu_preset render_profile video_quality'.split())
VISUAL=set('role_colors pavement_styles natural_materials_only image_features image_groups image_context_source name origin destination work_year imagery imagery_pixels imagery_detail web_source local_imagery elevation visual_quality water_texture water_texture_opacity water_names water_names_opacity water_animated headlights day_night night_start_s night_transition_s night_darkness night_signage_glow detail_textures texture_style texture_params texture_areas pavement_material existing_material shoulder_material joint_spacing_m project_contrast render_engine earthwork_look technical_textures style_profile progress_indicator callout_layout weather before_after vegetation_points vegetation_areas rail_smoke'.split())
PREVIEW_ONLY=set('preview_mode preview_time_s preview_center preview_width_m'.split())
FILES={'analysis':('analysis.json',),'editor':('editor.json',),'vectors':('vectors.json',),'preview':('preview.png','preview.json'),'video':('video.mp4','video.json'),'scene3d':('scene3d.json',),'video3d':('video3d.mp4','video3d.json')}

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def input_stamps(directory):
    d=Path(directory);geometry=[];presentation=[]
    candidates=[]
    for name in ('input.dxf','input.kmz','camadas','imagem_local','elevacao'):
        root=d/name
        if root.is_symlink():continue
        if root.is_file():candidates.append(root)
        elif root.is_dir():candidates.extend(root.rglob('*'))
    for f in sorted(candidates):
        rel=f.relative_to(d)
        if not f.is_file() or f.is_symlink():continue
        group=rel.parts[0]
        # Colar de nodata é cache derivado, não uma nova imagem de entrada.
        if group=='imagem_local' and f.name.startswith('.') and '.borda_' in f.name and f.suffix=='.npz':continue
        if group not in ('input.dxf','input.kmz','camadas','imagem_local','elevacao'):continue
        if f.name in ('grade.npy','grade.json') or f.name.startswith(('_converter','cache')):continue
        stat=f.stat();row=[rel.as_posix(),stat.st_size,stat.st_mtime_ns]
        (geometry if group in ('input.dxf','input.kmz','camadas') else presentation).append(row)
    return geometry,presentation

def engine_revision():
    # Recalcula na leitura para detectar atualizações de código sem depender da pasta de instalação.
    h=hashlib.sha256()
    for f in sorted(Path(__file__).parent.glob('*.py')):
        h.update(f.name.encode());h.update(f.read_bytes())
    return h.hexdigest()

def revisions(directory,settings=None):
    d=Path(directory)
    if settings is None:
        from .project_state import read_config
        settings=read_config(d)
    s=Settings.model_validate(settings.model_dump() if hasattr(settings,'model_dump') else settings).model_dump()
    inputs,images=input_stamps(d);engine=engine_revision()
    geo={k:v for k,v in s.items() if k not in TRAFFIC|CAMERA|VISUAL}
    geo['route_sources']=[{k:r.get(k) for k in ('id','name','enabled','points')} for r in s.get('route_alignments',[])];geometry=digest([engine,inputs,geo]);topology=digest([geometry,{k:s.get(k) for k in sorted(TRAFFIC-SIMULATION)}]);traffic=digest([topology,{k:s.get(k) for k in sorted(SIMULATION)}])
    # Os nomes de origem/destino e as texturas não mudam a geometria do editor.
    editor=digest([topology,{k:s.get(k) for k in ('pois','highlights','cities','oae_marks')}])
    presentation=digest([traffic,images,{k:s.get(k) for k in sorted(VISUAL)}])
    preview=digest([presentation,{k:s.get(k) for k in sorted(CAMERA)}])
    video=digest([presentation,{k:s.get(k) for k in sorted(CAMERA-PREVIEW_ONLY)}])
    scene3d=digest([presentation,s.get('duration_s')])
    return {'geometry':geometry,'topology':topology,'traffic':traffic,'presentation':presentation,'analysis':editor,'editor':editor,'vectors':geometry,'preview':preview,'video':video,'scene3d':scene3d,'video3d':scene3d}
