"""Contratos locais para orientação e correlações revisadas; sem envio externo."""
import json
from fastapi import APIRouter,HTTPException,Request
from fastapi.responses import PlainTextResponse,Response
from pydantic import Field,ValidationError
from .. import assistance as A,layer_profiles as LP,store
from .comum import dispatch_lock,idle

router=APIRouter()

async def payload(request):
    data=await request.body()
    if len(data)>2*1024*1024:raise HTTPException(413,'Arquivo de assistência excede 2 MiB.')
    try:return json.loads(data.decode('utf-8-sig'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Número não finito.')))
    except (ValueError,UnicodeError):raise HTTPException(422,'Envie um JSON válido, sem código ou blocos Markdown.')

def validate(model,data):
    try:return model.model_validate(data)
    except ValidationError as error:
        field='.'.join(map(str,error.errors()[0]['loc']))
        raise HTTPException(422,'Formato de assistência inválido no campo '+field+'. Confira o contrato; nada foi aplicado.')

@router.get('/api/projects/{pid}/assistencia')
def project_report(pid,mode:str='rules'):
    if mode not in ('normal','rules'):raise HTTPException(422,'Modo deve ser normal ou rules.')
    return A.report(store.directory(pid),pid,mode)

class PromptRequest(A.Strict):
    report_id:str=Field(pattern=r'^[0-9a-f]{24}$')
    task:str=Field(default='',max_length=4000)

@router.post('/api/projects/{pid}/assistencia/prompt')
def export_prompt(pid,body:PromptRequest):
    return PlainTextResponse(A.prompt(store.directory(pid),body.report_id,body.task),headers={'Content-Disposition':'attachment; filename="rodovia_assistencia_ia.md"'})

@router.post('/api/projects/{pid}/assistencia/resposta')
async def import_response(pid,request:Request):
    data=validate(A.AIResponse,await payload(request))
    return A.import_response(store.directory(pid),data.model_dump())

@router.post('/api/projects/{pid}/assistencia/revisar')
def review_changes(pid,body:A.ApplyRequest):return A.review(store.directory(pid),body)

@router.post('/api/projects/{pid}/assistencia/aplicar')
def apply_changes(pid,body:A.ApplyRequest):
    with dispatch_lock:
        idle(pid)
        return A.apply(store.directory(pid),body)

class Rule(A.Strict):
    pattern:str=Field(min_length=1,max_length=200)
    role:str=Field(min_length=1,max_length=40)
    material:str|None=Field(default=None,max_length=40)

class Profile(A.Strict):
    name:str=Field(min_length=1,max_length=80)
    rules:list[Rule]=Field(min_length=1,max_length=500)

class ProfileFile(A.Strict):
    format:str=Field(pattern=r'^rodovia-perfil-camadas-1$')
    profile:Profile

class SaveProfile(A.Strict):
    profile:Profile
    create:bool=True
    expected:str|None=Field(default=None,pattern=r'^[0-9a-f]{64}$')

def checked_profile(profile,ordered=False):
    value=profile.model_dump(exclude_none=True)
    seen={};unique=[]
    for rule in value['rules']:
        if rule['role'] not in LP.ROLE_LABELS or not A.compatible(rule['role'],rule.get('material')):raise HTTPException(422,'Perfil contém classe ou material incompatível com o motor.')
        key=LP.norm(rule['pattern'])
        if key in seen and not ordered and {k:v for k,v in seen[key].items() if k!='pattern'}!={k:v for k,v in rule.items() if k!='pattern'}:raise HTTPException(422,'Perfil contém regras conflitantes para o mesmo padrão.')
        if key not in seen:unique.append(rule)
        if key not in seen:seen[key]=rule
    value['rules']=unique
    return value

class ProfilePreview(A.Strict):
    report_id:str=Field(pattern=r'^[0-9a-f]{24}$')
    profile:Profile

@router.post('/api/projects/{pid}/assistencia/perfil_previa')
def profile_preview(pid,body:ProfilePreview):
    saved=A.snapshot(store.directory(pid),body.report_id);profile=checked_profile(body.profile);out=[]
    for layer in saved['catalog']['layers']:
        rule=next((r for r in profile['rules'] if LP.matches(r['pattern'],layer['name'])),None)
        if rule:out.append({'layer':layer['name'],'role':rule['role'],'material':rule.get('material'),'pattern':rule['pattern']})
    return {'rows':out,'notice':'Somente prévia; nenhuma classificação foi aplicada.'}

@router.get('/api/assistencia/perfis')
def profiles():
    out=[];warnings=[]
    for value in LP.load(store.ROOT):
        try:
            profile=checked_profile(Profile.model_validate({k:value[k] for k in ('name','rules')}),ordered=True)
            out.append({**profile,'builtin':bool(value.get('builtin')),'digest':A.digest(LP.validate(value)) if not value.get('builtin') else A.digest(profile)})
        except (ValueError,KeyError,HTTPException):warnings.append('Um perfil antigo não é compatível com o editor de assistência; seu arquivo foi preservado.')
    return {'profiles':out,'warnings':warnings}

@router.post('/api/assistencia/perfis')
def save_profile(body:SaveProfile):
    profile=checked_profile(body.profile)
    if not body.create and not body.expected:raise HTTPException(422,'Reabra o perfil para confirmar sua revisão antes de salvar.')
    result=LP.save(store.ROOT,profile,create_only=body.create,expected=body.expected)
    return {**result,'digest':A.digest(result)}

@router.post('/api/assistencia/perfis/importar')
async def import_profile(request:Request):
    value=validate(ProfileFile,await payload(request));profile=checked_profile(value.profile)
    return {'format':'rodovia-perfil-camadas-1','profile':profile,'notice':'Perfil validado para revisão; ainda não foi salvo nem aplicado.'}

@router.post('/api/assistencia/perfis/exportar')
def export_profile(body:Profile):
    value={'format':'rodovia-perfil-camadas-1','profile':checked_profile(body)}
    return Response(json.dumps(value,ensure_ascii=False,indent=2)+'\n',media_type='application/json',headers={'Content-Disposition':'attachment; filename="perfil_camadas_rodovia.json"'})
