import math
from typing import Literal
from pydantic import BaseModel, Field, model_validator, ConfigDict
from .migration import SCHEMA_VERSION, migrate

# 1.35: tipos de obra do PER (as 8 primeiras existiam antes; códigos não mudam).
WORK_KINDS=('oae','passarela','intersecao','via_marginal','correcao','fauna','onibus','outro','duplicacao','faixa_adicional','iluminacao','retorno','acesso',
 'acostamento','pavimento','drenagem','contencao','sinalizacao','defensa','ciclovia','calcada','pedagio','posto','cerca','alargamento_oae','travessia')

class Point(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    x: float
    y: float

class POI(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    title: str = Field(min_length=1, max_length=100)
    subtitle: str = Field(default='', max_length=160)
    kind: Literal[WORK_KINDS] = 'outro'
    x: float
    y: float
    km_m: float | None = None
    # auto: km calculado pelo estaqueamento; manual: km_m informado (referência oficial).
    km_mode: Literal['auto','manual'] = 'auto'
    # Ponto de ancoragem da linha de chamada (CRS do projeto). None = comportamento automático.
    anchor: Point | None = None
    bridge_span_m: float | None = Field(default=None,ge=10,le=160)
    bridge_width_m: float = Field(default=3,ge=1.5,le=8)
    bridge_angle_deg: float = Field(default=0,ge=-85,le=85)
    bridge_access: Literal['ramps','stairs','none'] = 'ramps'

    ramp_flight_m: float = Field(default=24,ge=10,le=80)
    bus_length_m: float = Field(default=30,ge=12,le=80)
    bus_depth_m: float = Field(default=3,ge=2.5,le=5)
    bus_side: Literal['right','left'] = 'right'

VEG_KINDS=('arvore','ipe','eucalipto','palmeira','arbusto','cerca_viva')
class VegPoint(BaseModel):
    """1.37: árvore/planta avulsa (clique ou pincel)."""
    model_config=ConfigDict(allow_inf_nan=False)
    x: float
    y: float
    kind: Literal[VEG_KINDS] = 'arvore'
    size_m: float = Field(default=7,ge=1,le=30)

class VegArea(BaseModel):
    """1.37: área com vegetação: plantas espalhadas pela densidade (por 1000 m²), sempre no mesmo lugar (semente)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Vegetação',min_length=1,max_length=80)
    kind: Literal[VEG_KINDS] = 'arvore'
    points: list[Point] = Field(min_length=3,max_length=2000)
    density: float = Field(default=6,ge=.2,le=60)
    size_m: float = Field(default=7,ge=1,le=30)
    seed: int = Field(default=1,ge=0,le=10**9)
    enabled: bool = True

class PedPath(BaseModel):
    """1.37: caminho de pedestres (calçada, trilha): pessoas andando nos dois sentidos."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Caminho de pedestres',min_length=1,max_length=80)
    points: list[Point] = Field(min_length=2,max_length=2000)
    people_per_100m: float = Field(default=3,ge=.2,le=40)
    enabled: bool = True

class CameraKey(BaseModel):
    """1.36: ponto-chave da câmera: centro e largura da vista (m), tempo parado e título opcional no cabeçalho."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    x: float
    y: float
    width_m: float = Field(default=600,ge=20,le=200000)
    hold_s: float = Field(default=3,ge=0,le=120)
    title: str = Field(default='',max_length=100)

class PERWork(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    description: str = Field(min_length=1,max_length=300)
    km_start_m: float = Field(ge=0)
    km_end_m: float = Field(ge=0)
    kind: Literal[WORK_KINDS] = 'outro'
    per_year: str = Field(default='',max_length=70)
    per_table: str = Field(default='',max_length=70)
    x: float | None = None
    y: float | None = None
    # manual: km da tabela PER; auto: km calculado a partir de X/Y pelo estaqueamento.
    km_mode: Literal['auto','manual'] = 'manual'
    # 1.35: lado, cronograma e exibição.
    side: Literal['ambos','direito','esquerdo'] = 'ambos'
    start_date: str = Field(default='',pattern=r'^(\d{4}-\d{2}-\d{2})?$')
    end_date: str = Field(default='',pattern=r'^(\d{4}-\d{2}-\d{2})?$')
    progress_pct: float | None = Field(default=None,ge=0,le=100)
    color: str = Field(default='',pattern=r'^(#[0-9a-fA-F]{6})?$')
    show: bool = True
    task: str = Field(default='',max_length=300)   # tarefa do cronograma ligada a esta obra
    @model_validator(mode='after')
    def validate_range(self):
        if self.start_date and self.end_date and self.end_date<self.start_date:raise ValueError('Término da obra anterior ao início.')
        if self.km_end_m<self.km_start_m:raise ValueError('Km final da obra anterior ao inicial.')
        if (self.x is None)!=(self.y is None):raise ValueError('Informe X e Y juntos.')
        return self

class TrafficPath(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Trajetória',max_length=100)
    points: list[Point] = Field(min_length=2,max_length=2000)
    kind: Literal['main','marginal','device','return'] = 'device'
    direction: Literal['auto','growing','decreasing','both'] = 'auto'
    level: int = Field(default=0,ge=-5,le=5)
    enabled: bool = True
    speed_kmh: float | None = Field(default=None,ge=5,le=130)   # 1.27

class Chainage(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    # off: km só quando digitado (comportamento 1.2); auto: começo geométrico do eixo e sentido do eixo;
    # manual: início/fim/sentido marcados no editor.
    mode: Literal['off','auto','manual'] = 'auto'
    # Ponto clicado sobre o eixo onde vale km_start_m. None = início geométrico do eixo.
    start: Point | None = None
    # Ponto final opcional (onde vale km_end_m); define o sentido quando existe.
    end: Point | None = None
    direction: Literal[1,-1] = 1
    # Ajuste proporcional: distribui a diferença entre km final informado e distância medida.
    calibrate: bool = False

class ControlPair(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    dxf: Point
    image: Point
    enabled: bool = True

class DxfAlignment(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    mode: Literal['translation','similarity'] = 'translation'
    pairs: list[ControlPair] = Field(default_factory=list,max_length=60)
    applied: bool = False

class DirectionMark(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    start: Point
    end: Point
    @model_validator(mode='after')
    def length(self):
        if ((self.end.x-self.start.x)**2+(self.end.y-self.start.y)**2)**.5<1:raise ValueError('A seta de sentido precisa ter pelo menos 1 m.')
        return self

class FlowOverride(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    x: float
    y: float
    action: Literal['reverse','disable','speed']
    enabled: bool = True
    speed_kmh: float | None = Field(default=None,ge=5,le=130)   # 1.27: limite de velocidade no trecho (ação 'speed')
    @model_validator(mode='after')
    def speed_ok(self):
        if self.action=='speed' and self.speed_kmh is None:raise ValueError('Velocidade do trecho: informe o limite em km/h (5 a 130).')
        return self

class RouteSection(BaseModel):
    """1.30: trecho de uma rota de veículos com tipo de pista próprio (início e fim em metros ao longo da rota)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Trecho',min_length=1,max_length=80)
    start_m: float = Field(default=0,ge=0)
    end_m: float = Field(default=0,ge=0)
    type: Literal['simples','dupla','unico'] = 'dupla'
    lanes: int = Field(default=1,ge=1,le=6)          # faixas por sentido (no sentido único: total)
    median_m: float = Field(default=0,ge=0,le=60)    # canteiro central na pista dupla
    @model_validator(mode='after')
    def order(self):
        if self.end_m<self.start_m:self.start_m,self.end_m=self.end_m,self.start_m
        return self


class LaneChangeSection(BaseModel):
    """1.40.4: trecho da rota onde a mudança de faixa é explicitamente permitida ou proibida.

    A geometria da rota nunca é alterada por esta regra; ela controla apenas o comportamento dos veículos.
    """
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Mudança de faixa',min_length=1,max_length=80)
    start_m: float = Field(default=0,ge=0)
    end_m: float = Field(default=0,ge=0)
    mode: Literal['allow','deny'] = 'allow'
    @model_validator(mode='after')
    def order(self):
        if self.end_m<self.start_m:self.start_m,self.end_m=self.end_m,self.start_m
        return self

class RouteAlignment(BaseModel):
    """1.30: alinhamento de rota dos veículos. As faixas são geradas como fluxos paralelos ao alinhamento:
    pista simples (um sentido de cada lado), pista dupla por sentido (com canteiro) ou sentido único,
    com trechos de tipos diferentes ao longo do mesmo alinhamento e transições suaves entre eles."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Rota',min_length=1,max_length=80)
    points: list[Point] = Field(min_length=2,max_length=20000)
    enabled: bool = True
    type: Literal['simples','dupla','unico'] = 'simples'   # tipo fora dos trechos
    lanes: int = Field(default=1,ge=1,le=6)
    median_m: float = Field(default=0,ge=0,le=60)
    lane_width_m: float = Field(default=3.5,ge=2.5,le=5)
    taper_m: float = Field(default=40,ge=5,le=300)          # comprimento das transições
    speed_kmh: float | None = Field(default=None,ge=5,le=130)
    level: int = Field(default=0,ge=-5,le=5)
    outside_pavement: bool = False                          # deixa os veículos andarem fora do pavimento do desenho
    source: str = 'cliques'
    sections: list[RouteSection] = Field(default_factory=list,max_length=100)
    # 1.40.4: ultrapassagem/mudança de faixa. "marked" é o padrão conservador: somente em trechos allow.
    lane_change: Literal['off','marked','safe'] = 'marked'
    lane_change_sections: list[LaneChangeSection] = Field(default_factory=list,max_length=200)
    @model_validator(mode='after')
    def disable_micro_route(self):
        # O limite de circulação pertence ao projeto; não altera a opção manual da rota.
        L=sum(math.hypot(b.x-a.x,b.y-a.y) for a,b in zip(self.points,self.points[1:]))
        if not math.isfinite(L) or L <= 0.0:self.enabled=False
        return self

class AdvanceZone(BaseModel):
    """1.27: trecho com velocidade de avanço própria da câmera (ex.: mais devagar sobre uma obra)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Trecho',min_length=1,max_length=80)
    start: Point
    end: Point
    speed_pct: float = Field(default=50,ge=10,le=500)   # % da velocidade normal (50 = metade, 200 = o dobro)
    enabled: bool = True

class SignagePaint(BaseModel):
    """1.29: aparência da sinalização horizontal (cores, desgaste e opacidade). Valores neutros = como antes."""
    model_config=ConfigDict(allow_inf_nan=False)
    white: str = Field(default='',pattern=r'^(#[0-9a-fA-F]{6})?$')
    yellow: str = Field(default='',pattern=r'^(#[0-9a-fA-F]{6})?$')
    wear: float = Field(default=0,ge=0,le=1)        # 0 = tinta nova; 1 = muito gasta
    opacity: float = Field(default=1,ge=.2,le=1)

class TextureArea(BaseModel):
    """1.29: textura própria numa região (talude, canteiro ou pavimento) sem mudar o tipo nem a geometria."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Textura',min_length=1,max_length=80)
    surface: Literal['talude_corte','talude_aterro','canteiro','pista_nova','pista_existente','acostamento','concreto'] = 'talude_corte'
    points: list[Point] = Field(min_length=3,max_length=5000)
    texture: 'TextureParam | None' = None
    enabled: bool = True

class ConnectionRule(BaseModel):
    """1.27: regra de ligação num cruzamento: proibir um movimento (de um trecho para outro) ou forçar uma ligação."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Ligação',min_length=1,max_length=80)
    a: Point            # ponto no trecho de chegada (perto do fim)
    b: Point            # ponto no trecho de saída (perto do início)
    action: Literal['deny','force'] = 'deny'
    enabled: bool = True

class OAEMark(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='OAE',min_length=1,max_length=100)
    start: Point
    end: Point
    level_m: float = Field(default=6.0,ge=-30,le=60)
    width_m: float = Field(default=14.0,ge=3,le=60)
    km_start_override_m: float | None = None
    km_end_override_m: float | None = None
    callout: bool = True
    # 1.11: tabuleiro desenhado por vértices (4 ou mais, polígono irregular) e sentido do tráfego sobre a OAE.
    polygon: list[Point] = Field(default_factory=list,max_length=200)
    direction: Literal['both','growing','decreasing'] = 'both'
    @model_validator(mode='after')
    def polygon_ok(self):
        if self.polygon and len(self.polygon)<4:raise ValueError('A OAE por vértices precisa de pelo menos 4 vértices.')
        return self

class NoConnectionZone(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Cruzamento sem conexão',max_length=100)
    kind: Literal['point','area'] = 'point'
    point: Point | None = None
    radius_m: float = Field(default=25.0,ge=2,le=300)
    points: list[Point] = Field(default_factory=list,max_length=2000)
    @model_validator(mode='after')
    def shape(self):
        if self.kind=='point' and self.point is None:raise ValueError('Cruzamento sem conexão: informe o ponto.')
        if self.kind=='area' and len(self.points)<3:raise ValueError('Cruzamento sem conexão: a área precisa de três vértices.')
        return self

class OverlayLayer(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = Field(pattern=r'^[0-9a-f]{32}$')
    name: str = Field(default='Camada DXF',min_length=1,max_length=100)
    original_name: str = Field(default='',max_length=260)
    enabled: bool = True
    order: int = 0
    color: str = Field(default='#ff9f1c',pattern=r'^#[0-9a-fA-F]{6}$')
    opacity: float = Field(default=.9,ge=0,le=1)
    line_width_m: float = Field(default=.6,ge=.05,le=20)
    fill: bool = False
    # Camada do DXF -> classe ('' = desenho com o estilo da camada; 'ignore' = não usar).
    roles: dict[str,str] = Field(default_factory=dict)
    crs: str | None = None
    alignment: DxfAlignment = Field(default_factory=DxfAlignment)

class LocalSource(BaseModel):
    """1.17: imagem adicional do mosaico local."""
    model_config=ConfigDict(allow_inf_nan=False)
    name: str = ''
    image: str = ''
    world: str | None = None
    prj: str | None = None
    crs: str | None = None
    enabled: bool = True
    nodata: Literal['borda','auto','none'] = 'borda'   # 1.39: borda = só branco 255/preto 0 ligados à beira
    # 1.19: ajuste fino por grips no editor (no CRS do projeto, em torno do centro da imagem). Neutro = original.
    shift_x: float = Field(default=0,ge=-2000,le=2000)
    shift_y: float = Field(default=0,ge=-2000,le=2000)
    rotation_deg: float = Field(default=0,ge=-30,le=30)
    scale: float = Field(default=1,ge=.8,le=1.25)

class LocalImagery(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    name: str = ''
    image: str = ''
    world: str | None = None
    prj: str | None = None
    crs: str | None = None
    # 1.17: mosaico (imagens adicionais), uso na camada de detalhe do vídeo e no editor, ajuste de cor.
    others: list[LocalSource] = Field(default_factory=list,max_length=60)
    detail: bool = True
    editor: bool = True
    nodata: Literal['borda','auto','none'] = 'borda'   # 1.39: borda = só branco 255/preto 0 ligados à beira
    brightness: float = Field(default=0,ge=-.5,le=.5)
    contrast: float = Field(default=0,ge=-.5,le=.5)
    saturation: float = Field(default=0,ge=-.5,le=.5)
    # 1.19: ajuste fino por grips no editor (no CRS do projeto, em torno do centro da imagem). Neutro = original.
    shift_x: float = Field(default=0,ge=-2000,le=2000)
    shift_y: float = Field(default=0,ge=-2000,le=2000)
    rotation_deg: float = Field(default=0,ge=-30,le=30)
    scale: float = Field(default=1,ge=.8,le=1.25)

class WebImagery(BaseModel):
    """1.19: fonte web alternativa à Esri atual (Esri Wayback por data, ou serviço XYZ/WMS indicado pelo usuário)."""
    model_config=ConfigDict(allow_inf_nan=False)
    source: Literal['esri','wayback','xyz','wms'] = 'esri'
    wayback_release: int | None = Field(default=None,ge=1,le=10**7)
    wayback_label: str = Field(default='',max_length=60)
    url: str = Field(default='',max_length=600)
    wms_layers: str = Field(default='',max_length=200)
    attribution: str = Field(default='',max_length=200)
    max_zoom: int = Field(default=19,ge=10,le=23)
    # 1.25: serviço escolhido no catálogo QuickMapServices (valores neutros = comportamento anterior).
    wms_version: Literal['1.3.0','1.1.1'] = '1.3.0'
    wms_format: Literal['image/jpeg','image/png'] = 'image/jpeg'
    qms_id: int | None = Field(default=None,ge=1,le=10**9)
    qms_name: str = Field(default='',max_length=120)
    terms_url: str = Field(default='',max_length=400)

class PNGExport(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    start_s: float = Field(default=0,ge=0,le=1800)
    end_s: float = Field(default=5,ge=0,le=1800)
    every_n_frames: int = Field(default=1,ge=1,le=300)
    rgba_layers: bool = False
    @model_validator(mode='after')
    def order(self):
        if self.end_s<self.start_s:raise ValueError('Sequência PNG: o fim deve ser posterior ao início.')
        return self

class Cabin(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    enabled: bool = False
    # Ponto clicado sobre uma trajetória validada: define o veículo, o sentido e o início do trecho.
    start: Point | None = None
    duration_s: float = Field(default=20.0,ge=3,le=600)
    eye_height_m: float = Field(default=1.25,ge=.8,le=4)
    fov_deg: float = Field(default=72.0,ge=40,le=110)
    pitch_deg: float = Field(default=4.0,ge=0,le=25)
    smoothing_s: float = Field(default=1.2,ge=0,le=5)
    speed_kmh: float | None = Field(default=None,ge=5,le=110)
    hood: bool = True

class Elevation(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    source: Literal['none','local','web'] = 'none'
    file: str | None = None
    world: str | None = None
    prj: str | None = None
    crs: str | None = None
    exaggeration: float = Field(default=1.0,ge=.5,le=3)
    hillshade: bool = False
    hillshade_opacity: float = Field(default=.35,ge=0,le=1)
    contours: bool = False
    contour_interval_m: float = Field(default=5.0,ge=.5,le=100)
    level_road: bool = True

class Highlight(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Destaque',min_length=1,max_length=80)
    category: Literal['edificacao','interferencia','poste','rede','drenagem','acesso','outro','rede_agua','gas','telecom','torre','arvore','cerca','placa','desapropriacao','ocupacao','escola','saude','comercio','curso_dagua','geotecnia','patrimonio','ponto_onibus','pedestre','acidente'] = 'outro'   # 1.35: mais categorias
    description: str = Field(default='',max_length=160)
    point: Point
    # Posição da caixa de informação (CRS). None = automática, ao lado do ponto.
    label: Point | None = None
    color: str = Field(default='',pattern=r'^(#[0-9a-fA-F]{6})?$')
    show_in_video: bool = True
    show_km: bool = True
    # Inclui o ponto como parada da câmera (cena de detalhe com o nome no cabeçalho).
    stop: bool = False
    # 1.26: caixa de chamada melhorada (valores neutros = como antes).
    style: Literal['cartao','compacto','etiqueta'] = 'cartao'
    text_scale: float = Field(default=1,ge=.6,le=2)
    image: str = Field(default='',max_length=60,pattern=r'^([0-9a-f]{16,40}\.(png|jpg))?$')
    start_s: float | None = Field(default=None,ge=0,le=1800)
    end_s: float | None = Field(default=None,ge=0,le=1800)
    leader: Literal['reta','cotovelo'] = 'reta'
    @model_validator(mode='after')
    def window(self):
        if self.start_s is not None and self.end_s is not None and self.end_s<=self.start_s:raise ValueError('Destaque: o fim da exibição deve ser depois do início.')
        return self

class Gantry(BaseModel):
    """1.26: pórtico de sinalização marcado por dois cliques (apoios), com a imagem da placa numa caixa de chamada."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Pórtico',min_length=1,max_length=80)
    description: str = Field(default='',max_length=160)
    kind: Literal['portico','semiportico','bandeira'] = 'portico'
    a: Point
    b: Point
    image: str = Field(default='',max_length=60,pattern=r'^([0-9a-f]{16,40}\.(png|jpg))?$')
    beam_width_m: float = Field(default=1.0,ge=.3,le=4)
    height_m: float = Field(default=7,ge=4,le=15)
    color: str = Field(default='',pattern=r'^(#[0-9a-fA-F]{6})?$')
    show_in_video: bool = True
    callout: bool = True
    label: Point | None = None
    start_s: float | None = Field(default=None,ge=0,le=1800)
    end_s: float | None = Field(default=None,ge=0,le=1800)
    text_scale: float = Field(default=1,ge=.6,le=2)
    @model_validator(mode='after')
    def span(self):
        d=((self.a.x-self.b.x)**2+(self.a.y-self.b.y)**2)**.5
        if d<2:raise ValueError(f'Pórtico “{self.name}”: os dois apoios estão a {d:.2f} m (mínimo 2 m).')
        if d>120:raise ValueError(f'Pórtico “{self.name}”: vão de {d:.0f} m (máximo 120 m).')
        if self.start_s is not None and self.end_s is not None and self.end_s<=self.start_s:raise ValueError('Pórtico: o fim da exibição deve ser depois do início.')
        return self

class City(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Cidade',min_length=1,max_length=80)
    point: Point
    kind: str = Field(default='',max_length=30)
    population: int | None = Field(default=None,ge=0)
    source: Literal['auto','manual'] = 'manual'
    show: bool = True

class LaneBlock(BaseModel):
    """1.12: interdição de faixa (área desenhada). Parcial reduz a velocidade e a capacidade; total fecha e desvia."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Interdição',min_length=1,max_length=80)
    points: list[Point] = Field(min_length=3,max_length=200)
    mode: Literal['partial','total'] = 'partial'
    speed_kmh: float = Field(default=20,ge=5,le=80)
    start_s: float = Field(default=0,ge=0,le=1800)
    end_s: float | None = Field(default=None,ge=0,le=1800)
    show: bool = True

class CrossingZone(BaseModel):
    """1.12: local onde a travessia do canteiro é permitida (retorno indicado) ou proibida."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Travessia',min_length=1,max_length=100)
    mode: Literal['allow','deny'] = 'allow'
    kind: Literal['point','area'] = 'point'
    point: Point | None = None
    radius_m: float = Field(default=20,ge=2,le=300)
    points: list[Point] = Field(default_factory=list,max_length=200)
    @model_validator(mode='after')
    def geometry(self):
        if self.kind=='point' and self.point is None:raise ValueError('Travessia por ponto precisa do ponto.')
        if self.kind=='area' and len(self.points)<3:raise ValueError('Travessia por área precisa de 3 vértices.')
        return self

class Crosswalk(BaseModel):
    """1.15: faixa de pedestre marcada por dois pontos (de um bordo ao outro da pista)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Faixa de pedestre',min_length=1,max_length=80)
    a: Point
    b: Point
    width_m: float = Field(default=4.0,ge=2,le=10)
    show: bool = True

class HatchArea(BaseModel):
    """1.15: área zebrada desenhada pelo operador (gores, ilhas pintadas, início de canteiro)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Zebrado',min_length=1,max_length=80)
    points: list[Point] = Field(min_length=3,max_length=300)
    color: Literal['white','yellow'] = 'white'
    angle_deg: float | None = Field(default=None,ge=-360,le=360)
    spacing_m: float = Field(default=2.6,ge=1,le=10)

class SignMark(BaseModel):
    """1.15: placa vertical (regulamentação, advertência, obras, indicação, serviço)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    point: Point
    code: Literal['R-1','R-2','R-19','A','OBRAS','I','S'] = 'I'
    text: str = Field(default='',max_length=40)
    heading_deg: float | None = Field(default=None,ge=-360,le=360)
    show: bool = True

class LaneZone(BaseModel):
    """1.15: número de faixas informado num trecho (substitui o cálculo pela largura)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Faixas',min_length=1,max_length=80)
    points: list[Point] = Field(min_length=3,max_length=300)
    lanes: int = Field(default=2,ge=1,le=6)

class AccessMark(BaseModel):
    """1.18: acesso rodoviário com taper de entrada (desaceleração) e de saída (aceleração)."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Acesso',min_length=1,max_length=80)
    points: list[Point] = Field(min_length=2,max_length=300)
    width_m: float = Field(default=7.0,ge=3,le=20)
    lane_width_m: float = Field(default=3.5,ge=2.5,le=5)
    taper_in_m: float = Field(default=60,ge=0,le=300)
    taper_out_m: float = Field(default=60,ge=0,le=300)
    mode: Literal['both','in','out'] = 'both'
    enabled: bool = True

class PavementArea(BaseModel):
    """1.20: área desenhada ou selecionada no editor que passa a ser pista nova, pista existente ou acostamento."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Área',min_length=1,max_length=80)
    kind: Literal['pavement','existing_pavement','shoulder'] = 'pavement'
    points: list[Point] = Field(min_length=3,max_length=5000)
    source: Literal['drawn','picked'] = 'drawn'
    material: Literal['auto','flexivel','rigido'] = 'auto'   # 1.21: auto = padrão do projeto para o tipo
    enabled: bool = True
    texture: 'TextureParam | None' = None   # 1.27: textura própria desta área (vazio = a do tipo)

class ShoulderMark(BaseModel):
    """1.20: acostamento ao longo do bordo da pista, entre um ponto de início e um de fim, com largura."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='Acostamento',min_length=1,max_length=80)
    start: Point
    end: Point
    width_m: float = Field(default=2.5,ge=.5,le=6)
    enabled: bool = True

class PavementStyle(BaseModel):
    """1.21: representação gráfica escolhida para um tipo de superfície (substitui a automática)."""
    model_config=ConfigDict(allow_inf_nan=False)
    pattern: Literal['auto','solido','diagonal','cruzada','pontilhado','placas'] = 'auto'
    fill: str = Field(default='',pattern=r'^(#[0-9a-fA-F]{6})?$')
    hatch: str = Field(default='',pattern=r'^(#[0-9a-fA-F]{6})?$')
    spacing_m: float = Field(default=3,ge=.3,le=20)
    angle_deg: float = Field(default=45,ge=-90,le=90)
    line_m: float = Field(default=.15,ge=.02,le=1)

class TextureParam(BaseModel):
    """1.24: ajuste de textura de uma superfície (multiplicadores; 1 = padrão)."""
    model_config=ConfigDict(allow_inf_nan=False)
    grao: float = Field(default=1,ge=0,le=3)
    tom: float = Field(default=1,ge=0,le=3)
    remendos: float = Field(default=1,ge=0,le=3)
    fissuras: float = Field(default=1,ge=0,le=3)
    brilho: float = Field(default=0,ge=-.3,le=.3)

PavementArea.model_rebuild()
TextureArea.model_rebuild()

class HatchRole(BaseModel):
    """1.24: tipo atribuído a uma assinatura de hachura do DXF (camada | padrão | cor)."""
    model_config=ConfigDict(allow_inf_nan=False)
    role: Literal['pavement','existing_pavement','shoulder','median','barrier','oae','cut','fill','water','domain','ignore']
    material: Literal['auto','flexivel','rigido'] = 'auto'

class CustomAxis(BaseModel):
    """1.22: alinhamento (eixo de referência) definido por cliques sobre o eixo da via no editor."""
    model_config=ConfigDict(allow_inf_nan=False)
    name: str = Field(default='Alinhamento do editor',min_length=1,max_length=80)
    points: list[Point] = Field(min_length=2,max_length=20000)
    smooth: bool = True
    enabled: bool = True
    source: Literal['cliques','linha','continua'] = 'cliques'   # 1.26: como foi criado

class LaneRange(BaseModel):
    """1.18: faixa adicional (ex.: 3ª faixa) entre um ponto de início e um de fim marcados na pista."""
    model_config=ConfigDict(allow_inf_nan=False)
    id: str = ''
    name: str = Field(default='3ª faixa',min_length=1,max_length=80)
    start: Point
    end: Point
    lanes: int = Field(default=3,ge=1,le=6)

from .transport_models import Railway,TrafficSignal,SignalLink,validate_network

class Settings(BaseModel):
    railways:list[Railway]=Field(default_factory=list,max_length=50)
    traffic_signals:list[TrafficSignal]=Field(default_factory=list,max_length=100)
    signal_links:list[SignalLink]=Field(default_factory=list,max_length=100)
    @model_validator(mode="after")
    def transport_network(self):return validate_network(self)

    model_config=ConfigDict(allow_inf_nan=False)
    schema_version: int = SCHEMA_VERSION
    name: str = Field(default='Novo trecho', min_length=1, max_length=100)
    origin: str = Field(default='Origem', max_length=100)
    destination: str = Field(default='Destino', max_length=100)
    km_start_m: float = 0
    km_end_m: float = 1000
    reference_length_m: float | None = Field(default=None, gt=0)
    work_year: str = Field(default='A informar', max_length=70)
    crs: str = 'EPSG:31983'  # valor legado para compatibilidade; a interface deve detectar/solicitar confirmação e nunca assumir este CRS em cálculo genérico
    coordinates_confirmed: bool = False
    reverse_axis: bool = False
    units_to_m: float = Field(default=1, gt=0, le=1000)
    width: Literal[1280,1920,2560,3840] = 2560   # 1.32: 3840 = 4K
    # 1.32: qualidade do vídeo. padrao = como até a 1.31; alta = imagem de fundo mais nítida, veículos sem serrilhado e
    # menos compressão; maxima = além disso, superamostragem do quadro (1,5×), detalhe a 0,1 m e ladrilhos Esri nível 20.
    video_quality: Literal['padrao','alta','maxima'] = 'alta'
    fps: Literal[24,30] = 30
    duration_s: float = Field(default=202, ge=3, le=1800)
    view_width_m: float = Field(default=750, ge=80, le=20000)
    imagery: Literal['cache','esri','neutral','local'] = 'esri'
    local_imagery: LocalImagery = Field(default_factory=LocalImagery)
    web_imagery: WebImagery = Field(default_factory=WebImagery)
    preview_mode: Literal['overview','video','custom'] = 'overview'
    preview_center: Point | None = None
    preview_width_m: float | None = Field(default=None, ge=5, le=50000)
    preview_time_s: float = Field(default=30, ge=0, le=1800)
    imagery_pixels: Literal[2048,4096,8192] = 4096
    layers: dict[str,list[str]] = Field(default_factory=dict)
    pois: list[POI] = Field(default_factory=list, max_length=500)
    exclusions: list[list[Point]] = Field(default_factory=list, max_length=100)
    works: list[PERWork] = Field(default_factory=list,max_length=1000)
    per_callouts: bool = True
    # 1.35: obras do PER no vídeo — chamada (só a caixa, como antes) ou trecho (faixa colorida do km inicial ao final + caixa).
    per_display: Literal['chamada','trecho'] = 'trecho'
    # 1.35: linha do tempo pelo cronograma: o vídeo percorre as datas e mostra cada obra prevista, em execução ou concluída.
    schedule_mode: Literal['off','linha_do_tempo'] = 'off'
    schedule_start: str = Field(default='',pattern=r'^(\d{4}-\d{2}-\d{2})?$')
    schedule_end: str = Field(default='',pattern=r'^(\d{4}-\d{2}-\d{2})?$')
    schedule_show_planned: bool = True
    traffic_paths: list[TrafficPath] = Field(default_factory=list,max_length=100)
    traffic_network_preview: bool = False
    derive_traffic_paths: bool = True
    route_directions: dict[str,Literal['auto','forward','reverse','off']] = Field(default_factory=dict)
    encoder: Literal['auto','nvenc','cpu'] = 'auto'
    cpu_preset: Literal['fast','veryfast'] = 'veryfast'
    short_video_mode: Literal['auto','tour'] = 'auto'
    hydrography: bool = True
    traffic: bool = True
    traffic_speed_kmh: float = Field(default=70, ge=5, le=110)
    chainage: Chainage = Field(default_factory=Chainage)
    dxf_alignment: DxfAlignment = Field(default_factory=DxfAlignment)
    direction_marks: list[DirectionMark] = Field(default_factory=list,max_length=500)
    flow_overrides: list[FlowOverride] = Field(default_factory=list,max_length=1000)
    oae_marks: list[OAEMark] = Field(default_factory=list,max_length=200)
    no_connection_zones: list[NoConnectionZone] = Field(default_factory=list,max_length=200)
    overlays: list[OverlayLayer] = Field(default_factory=list,max_length=30)
    # Qualidade visual (1.5). 'classic' reproduz o desenho anterior.
    visual_quality: Literal['classic','enhanced'] = 'enhanced'
    water_texture: bool = True
    water_texture_opacity: float = Field(default=.65,ge=0,le=1)
    water_names: bool = True
    water_names_opacity: float = Field(default=1,ge=0,le=1)
    water_animated: bool = False
    headlights: bool = False
    cabin: Cabin = Field(default_factory=Cabin)
    # Desempenho (1.7): 0 = automático pelos núcleos e memória do computador; 1 = um processo.
    render_workers: int = Field(default=0,ge=0,le=32)
    render_profile: Literal['final','rapido'] = 'final'
    elevation: Elevation = Field(default_factory=Elevation)
    highlights: list[Highlight] = Field(default_factory=list,max_length=500)
    png_export: PNGExport = Field(default_factory=PNGExport)
    # 1.10: sinalização limpa, setas por km/conflito, marcos de km, seta de sentido e cidades.
    signage_style: Literal['clean','previous'] = 'clean'
    flow_arrows: Literal['km_conflicts','dense','off'] = 'km_conflicts'
    flow_arrow_spacing_m: float = Field(default=1000,ge=100,le=5000)
    clean_areas: list[list[Point]] = Field(default_factory=list,max_length=300)
    km_markers: bool = True
    direction_badge: bool = True
    median_grass: bool = True
    cities: list[City] = Field(default_factory=list,max_length=100)
    cities_show: bool = True
    cities_radius_km: float = Field(default=25,ge=1,le=150)
    # 1.11: detalhe em alta resolução quando a câmera se aproxima.
    imagery_detail: Literal['auto','off'] = 'auto'
    detail_textures: bool = True
    # 1.12: tráfego simulado (sem colisão), densidade, interdições e travessias do canteiro.
    traffic_model: Literal['simulado','anterior'] = 'simulado'
    traffic_density: float = Field(default=1.0,ge=.2,le=8)
    # 1.40.5: capacidade e reação a veículos pesados. Mantidos neutros para projetos antigos.
    traffic_capacity_vphpl: float = Field(default=1900,gt=0,le=20000)
    traffic_demand_vphpl: float | None = Field(default=None,gt=0,le=20000)
    queue_capacity_model: bool = True
    heavy_vehicle_reaction: bool = True
    median_crossing: Literal['returns','marked','free'] = 'returns'
    # 1.39: trechos curtos (ramos do esqueleto nos encontros) abaixo disto não entram nas rotas (sem ziguezague); 0 = como antes.
    min_route_segment_m: float = Field(default=50,ge=0,le=500)
    crossing_zones: list[CrossingZone] = Field(default_factory=list,max_length=200)
    lane_blocks: list[LaneBlock] = Field(default_factory=list,max_length=100)
    # 1.13: transição dia/noite (faróis e sinalização em destaque).
    day_night: Literal['off','transition','night'] = 'off'
    night_start_s: float = Field(default=40,ge=0,le=1800)
    night_transition_s: float = Field(default=8,ge=.5,le=120)
    night_darkness: float = Field(default=.78,ge=.3,le=.95)
    night_signage_glow: bool = True
    # 1.14: ajustes por tipo de camada (cores) e talude automático para hachuras sem tipo.
    role_colors: dict[str,str] = Field(default_factory=dict)
    auto_earthworks: bool = True
    # 1.15: sinalização completa. 'basic' reproduz a sinalização da 1.14.
    signage_detail: Literal['full','basic'] = 'full'
    lane_width_m: float = Field(default=3.5,ge=2.5,le=5)
    lane_arrows: bool = True
    gore_hatch: bool = True
    stop_lines: bool = True
    auto_signs: bool = True
    dxf_signage: Literal['replace','add'] = 'replace'
    crosswalks: list[Crosswalk] = Field(default_factory=list,max_length=300)
    hatch_areas: list[HatchArea] = Field(default_factory=list,max_length=300)
    signs: list[SignMark] = Field(default_factory=list,max_length=1000)
    lane_zones: list[LaneZone] = Field(default_factory=list,max_length=300)
    # 1.18: controle do excesso de setas (repetição por faixa só antes de saídas/acessos; distância mínima).
    lane_arrow_repeat: Literal['conflicts','all','off'] = 'conflicts'
    layer_split: Literal['auto','off','all'] = 'auto'
    accesses: list[AccessMark] = Field(default_factory=list,max_length=200)
    # 1.20: veículos em linha reta, sentido pelo eixo, áreas de pavimento e acostamentos marcados.
    vehicle_paths: Literal['smooth','anterior'] = 'smooth'
    # Perfil "Apresentação técnica": hachuras de pista nova/existente/acostamento, indicador de progresso e voo contínuo.
    style_profile: Literal['padrao','tecnico'] = 'padrao'
    progress_indicator: bool = False
    camera_mode: Literal['obras','continuo','pontos'] = 'obras'
    # 1.36: câmera por pontos-chave (voo suave entre enquadramentos marcados no editor; usada com camera_mode='pontos').
    camera_keys: list[CameraKey] = Field(default_factory=list,max_length=60)
    # 1.36: clima, sombras pelo sol e comparação antes/depois (desligados = vídeo como antes).
    weather: Literal['limpo','nublado','chuva','neblina'] = 'limpo'
    weather_intensity: float = Field(default=.6,ge=.1,le=1)
    sun_shadows: bool = False
    sun_hour: float = Field(default=15,ge=6,le=18)
    before_after: bool = False
    before_after_s: float = Field(default=8,ge=3,le=30)
    # 1.37: vegetação, pedestres e mais tipos de veículo.
    vegetation_points: list[VegPoint] = Field(default_factory=list,max_length=20000)
    vegetation_areas: list[VegArea] = Field(default_factory=list,max_length=500)
    pedestrian_paths: list[PedPath] = Field(default_factory=list,max_length=300)
    pedestrians: bool = True            # pessoas nas faixas de pedestre, passarelas e caminhos
    vehicle_mix: Literal['classico','variado'] = 'variado'   # variado: carros, motos, vans, caminhões, carretas e ônibus
    # 1.21: pavimento flexível (asfalto) ou rígido (concreto com juntas), texturas no modo técnico e contraste projeto × imagem.
    pavement_material: Literal['flexivel','rigido'] = 'flexivel'
    existing_material: Literal['flexivel','rigido'] = 'flexivel'
    shoulder_material: Literal['flexivel','rigido'] = 'flexivel'
    joint_spacing_m: float = Field(default=5,ge=2,le=10)
    technical_textures: bool = False
    project_contrast: float = Field(default=0,ge=0,le=1)
    pavement_styles: dict[Literal['pavement','existing_pavement','shoulder'],PavementStyle] = Field(default_factory=dict)
    custom_axis: CustomAxis | None = None
    gantries: list[Gantry] = Field(default_factory=list,max_length=300)
    connection_rules: list[ConnectionRule] = Field(default_factory=list,max_length=500)   # 1.27
    signage_paint: SignagePaint = Field(default_factory=SignagePaint)   # 1.29
    texture_areas: list[TextureArea] = Field(default_factory=list,max_length=200)   # 1.29
    advance_zones: list[AdvanceZone] = Field(default_factory=list,max_length=200)   # 1.27: velocidade de avanço por trecho
    route_alignments: list[RouteAlignment] = Field(default_factory=list,max_length=50)   # 1.30: rotas dos veículos
    advance_mode: Literal['duracao','velocidade'] = 'duracao'   # 1.27: a duração do vídeo é digitada ou calculada pela velocidade
    advance_speed_kmh: float = Field(default=150,ge=5,le=5000)   # 1.27: velocidade de avanço sobre a imagem (modo 'velocidade')
    curve_speed: bool = True   # 1.27: veículos reduzem nas curvas fechadas e ligações (projetos antigos: desligado)
    hidden_layers: list[str] = Field(default_factory=list,max_length=3000)   # 1.26: some no editor e no vídeo
    frozen_layers: list[str] = Field(default_factory=list,max_length=3000)   # 1.26: travada no editor; no vídeo aparece pronta desde o início
    callout_layout: Literal['auto','anterior'] = 'auto'   # 1.26: caixas sem sobreposição; 'anterior' = como na 1.25
    render_engine: Literal['otimizado','anterior'] = 'otimizado'   # 1.24: 'anterior' reproduz os quadros da 1.23
    hatch_roles: dict[str,HatchRole] = Field(default_factory=dict)
    hatch_auto: bool = True   # hachuras de camadas não mapeadas recebem o tipo sugerido (projetos novos)
    texture_params: dict[Literal['pista_nova','pista_existente','concreto','acostamento','canteiro','trilhas','talude_corte','talude_aterro'],TextureParam] = Field(default_factory=dict)
    direction_reference: Literal['axis','anterior'] = 'axis'
    pavement_areas: list[PavementArea] = Field(default_factory=list,max_length=300)
    shoulder_marks: list[ShoulderMark] = Field(default_factory=list,max_length=300)
    # 1.18: faixas por sentido nas pistas principais (0 = pela largura); o restante é acostamento.
    lanes_per_direction: int = Field(default=2,ge=0,le=6)
    lane_ranges: list[LaneRange] = Field(default_factory=list,max_length=300)
    arrow_min_gap_m: float = Field(default=25,ge=0,le=500)  # 0 = sem afastamento mínimo (igual à 1.17)
    # 1.16: texturas. 'anterior' reproduz a 1.15; 'realistic' acrescenta agregado, remendos, fissuras,
    # trilhas de roda, acostamento e cor da imagem detalhada casada com o mosaico.
    texture_style: Literal['artistico','realistic','anterior'] = 'artistico'   # 1.34: artístico realista (novos projetos)
    earthwork_look: Literal['hatch','natural'] = 'hatch'
    detail_resolution_m: Literal[0.2,0.1] = 0.2
    @model_validator(mode='before')
    @classmethod
    def upgrade(cls,data):
        return migrate(data)
    @model_validator(mode='after')
    def ranges(self):
        if self.km_end_m <= self.km_start_m:
            raise ValueError('Km final deve ser maior que o inicial. O sentido do eixo é ajustado separadamente.')
        if self.reference_length_m is None:
            self.reference_length_m = self.km_end_m-self.km_start_m
        import re as _re
        for k,v in self.role_colors.items():
            if not _re.fullmatch(r'#[0-9a-fA-F]{6}',v or ''):raise ValueError(f'Cor inválida para {k}: use #RRGGBB.')
        if any(len(p)<3 for p in self.clean_areas):
            raise ValueError('Cada área sem sinalização precisa de pelo menos três vértices.')
        if any(len(p)<3 for p in self.exclusions):
            raise ValueError('Cada área de limpeza precisa de pelo menos três vértices.')
        return self
