"""Versão de esquema da configuração e migração automática de projetos antigos.

v1 (até 1.2): sem campo schema_version.
v3 (1.3): estaqueamento, alinhamento DXF, sentidos, fluxos, OAE e cruzamentos sem conexão.
v4 (1.4): camadas DXF adicionais, imagem georreferenciada local, exportação PNG.
v5 (1.5): qualidade visual (asfalto, OAE, água em duas camadas, veículos por tipo, faróis).
v6 (1.6): vista da cabine.
v7 (1.7): processos paralelos, perfil rápido e elevação do terreno.
v8 (1.8): estaqueamento automático/manual com fim e sentido; destaques (pontos especiais).
v9 (1.10): sinalização limpa, setas por km/conflito, áreas sem sinalização, marcos de km, seta de sentido, grama do canteiro e cidades.
v10 (1.11): imagem e texturas em alta resolução (ladrilhos de detalhe); OAE por polígono (4+ vértices) e sentido.
v11 (1.12): tráfego simulado sem colisão, densidade, interdições de faixa, travessias do canteiro; sinalização limpa em todo o modelo.
v12 (1.13): transição dia/noite com faróis e sinalização em destaque.
v13 (1.14): mapeamento de camadas sem regras fixas (pista existente explícita), novos tipos (bordo, hidrografia, talude), cores por tipo.
Os campos novos têm valores padrão; a migração só converte o que muda de significado.
"""
SCHEMA_VERSION=31
_MOJIBAKE=('Ã','â€','Â')

def repair_text(value):
    """Corrige textos UTF-8 lidos como cp1252 (ex.: 'OAE â€¢ Passagem' -> 'OAE • Passagem')."""
    if not isinstance(value,str) or not any(m in value for m in _MOJIBAKE):return value
    try:fixed=value.encode('cp1252').decode('utf-8')
    except (UnicodeEncodeError,UnicodeDecodeError):return value
    return fixed

def _repair(obj):
    if isinstance(obj,str):return repair_text(obj)
    if isinstance(obj,list):return [_repair(v) for v in obj]
    if isinstance(obj,dict):return {k:_repair(v) for k,v in obj.items()}
    return obj

import re as _re
_BAD_NAME=_re.compile(r'[<>\x00-\x1f\x7f]')
def clean_name(value,fallback):
    """1.29: nome sem espaços nas pontas, sem caracteres inválidos e com pelo menos uma letra ou número."""
    if not isinstance(value,str):return value
    v=_re.sub(r'\s+',' ',_BAD_NAME.sub('',value)).strip()[:80]
    return v if any(ch.isalnum() for ch in v) else fallback

def _names(obj,fallback='Sem nome'):
    if isinstance(obj,list):return [_names(v,fallback) for v in obj]
    if isinstance(obj,dict):
        out={}
        for k,v in obj.items():
            if k in ('name','title') and isinstance(v,str):out[k]=clean_name(v,fallback)
            elif isinstance(v,(list,dict)):out[k]=_names(v,fallback)
            else:out[k]=v
        return out
    return obj

def migrate(data):
    if not isinstance(data,dict):return data
    # Sem versão: configuração salva por versão antiga (tem km/camadas) ou projeto novo (só alguns campos).
    version=data.get('schema_version') or (1 if any(k in data for k in ('km_start_m','layers')) else SCHEMA_VERSION)
    if version>SCHEMA_VERSION:
        raise ValueError(f'Configuração criada por versão mais nova do aplicativo (esquema {version}). Atualize o Rodovia Studio.')
    data=_repair(dict(data))
    # 1.29: nomes vazios ou só com símbolos viram um nome válido (projetos antigos e gravações externas).
    top=data.get('name');data=_names(data)
    if isinstance(top,str):data['name']=clean_name(top,'Novo trecho')
    if version<3:
        # Até 1.2 o km de uma intervenção era sempre digitado: preserva como referência manual.
        pois=[]
        for p in data.get('pois') or []:
            if isinstance(p,dict):
                p=dict(p);p.setdefault('km_mode','manual' if p.get('km_m') is not None else 'auto')
            pois.append(p)
        data['pois']=pois
    if version<8:
        # Sem início marcado: 'off' (km só quando digitado, como antes); com início: 'manual'.
        c=dict(data.get('chainage') or {})
        c.setdefault('mode','manual' if c.get('start') else 'off');data['chainage']=c
    if version<13 and isinstance(data.get('layers'),dict):
        # Até a 1.13 uma camada de 'pavement' com EXIST no nome virava pista existente por regra fixa:
        # agora isso fica explícito no mapeamento do projeto (resultado idêntico).
        import unicodedata
        nrm=lambda v:''.join(c for c in unicodedata.normalize('NFKD',str(v).upper()) if not unicodedata.combining(c))
        lay={k:list(v) for k,v in data['layers'].items()};pav=lay.get('pavement',[])
        ex=[n for n in pav if 'EXIST' in nrm(n)]
        if ex:
            lay['pavement']=[n for n in pav if n not in ex];lay['existing_pavement']=list(dict.fromkeys(lay.get('existing_pavement',[])+ex))
            data['layers']=lay
    if version<17 and data.get('layers') and 'layer_split' not in data:
        # 1.18: projetos já mapeados mantêm os nomes de camada (sem separar a camada 0 por cor/tipo).
        data['layer_split']='off'
    if version<20 and data.get('style_profile')=='tecnico' and 'technical_textures' not in data:
        # 1.21: o modo técnico passou a desenhar hachuras limpas; projetos 1.20 mantêm as texturas por cima.
        data['technical_textures']=True
    if version<22 and 'hatch_auto' not in data:
        # 1.24: projetos anteriores continuam sem a leitura automática de hachuras (resultado idêntico); dá para ligar.
        data['hatch_auto']=False
    if version<23 and 'callout_layout' not in data:
        # 1.26: caixas de chamada com posição automática sem sobreposição; projetos anteriores mantêm o desenho da 1.25.
        data['callout_layout']='anterior'
    if version<24 and 'curve_speed' not in data:
        # 1.27: redução de velocidade nas curvas; projetos anteriores mantêm o movimento da 1.26.
        data['curve_speed']=False
    if version<26 and 'video_quality' not in data:
        # 1.32: projetos anteriores continuam com a qualidade de antes (vídeo idêntico); dá para escolher Alta/Máxima.
        data['video_quality']='padrao'
    if version<27 and 'texture_style' not in data:
        # 1.34: o padrão passou a ser “artístico realista”; projetos anteriores mantêm as texturas realistas de antes.
        data['texture_style']='realistic'
    if version<28 and 'per_display' not in data:
        # 1.35: obras do PER passaram a aparecer como trecho; projetos anteriores mantêm só a caixa de chamada (vídeo idêntico).
        data['per_display']='chamada'
    if version<29:
        # 1.37: projetos anteriores mantêm a frota (carros, caminhões, ônibus) e ficam sem pedestres (vídeo idêntico).
        data.setdefault('vehicle_mix','classico');data.setdefault('pedestrians',False)
    if version<30:
        # 1.39 (pedido do usuário): as bordas sem dados passam a começar só no branco 255/preto 0 ligados à beira da imagem
        # (antes: ≥253 e ≤3 em qualquer lugar, o que furava telhados e pinturas). A opção anterior continua em “Anterior”.
        li=data.get('local_imagery')
        if isinstance(li,dict):
            for o in [li]+[x for x in li.get('others') or [] if isinstance(x,dict)]:
                if o.get('nodata') in (None,'auto'):o['nodata']='borda'
    c=data.get('chainage')
    if isinstance(c,dict) and c.get('start') and 'mode' not in c:data['chainage']={**c,'mode':'manual'}  # início informado sem modo = manual
    data['schema_version']=SCHEMA_VERSION
    return data
