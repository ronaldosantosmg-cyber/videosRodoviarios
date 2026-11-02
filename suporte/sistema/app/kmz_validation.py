"""KMZ: limita somente o XML processado, sem expandir as imagens anexas."""
import zipfile,re,xml.etree.ElementTree as ET
from pathlib import PurePosixPath

MAX_KML=256*1024*1024
MAX_FILES=20000

def documents(path):
    try:
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist()
            if len(infos)>MAX_FILES:raise ValueError('KMZ contém mais de 20.000 entradas. Divida o arquivo.')
            names=[];size=0
            for info in infos:
                name=info.filename.replace('\\','/');parts=PurePosixPath(name).parts
                if name.startswith('/') or '..' in parts or re.match(r'^[A-Za-z]:',name) or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('KMZ contém caminho interno inseguro ou link simbólico.')
                if info.flag_bits&1:raise ValueError('KMZ protegido por senha. Exporte novamente sem criptografia.')
                if name.lower().endswith('.kml'):
                    size+=info.file_size;names.append(info)
            if not names:raise ValueError('KMZ não contém documento .kml. Confira se foi exportado como KMZ, e não apenas renomeado.')
            if size>MAX_KML:raise ValueError(f'Os documentos KML internos somam {size/1048576:.1f} MB; limite de {MAX_KML/1048576:g} MB de XML. Imagens anexas não entram nesse limite.')
            used=0
            for info in names:
                chunks=[]
                with archive.open(info) as member:
                    while chunk:=member.read(1024*1024):
                        used+=len(chunk)
                        if used>MAX_KML:raise ValueError('Documentos KML descompactados excedem 100 MB de XML.')
                        chunks.append(chunk)
                raw=b''.join(chunks)
                scan=raw.replace(b'\x00',b'').upper()
                if b'<!DOCTYPE' in scan or b'<!ENTITY' in scan:raise ValueError('KML com DTD/entidades não é aceito. Exporte um KML sem referências XML externas.')
                try:root=ET.fromstring(raw)
                except ET.ParseError as exc:raise ValueError('Documento KML interno malformado: '+str(exc)[:180]) from exc
                if root.tag.rsplit('}',1)[-1].lower()!='kml':raise ValueError('O XML interno não tem raiz KML válida.')
                yield info.filename,root
    except zipfile.BadZipFile as exc:raise ValueError('KMZ corrompido ou não é ZIP válido. Exporte novamente no programa de origem.') from exc
    except (RuntimeError,NotImplementedError) as exc:raise ValueError('Não foi possível ler a compressão / proteção do KMZ. Exporte como ZIP/KMZ sem senha.') from exc

class _LimitedXML:
    def __init__(self,member,budget):self.member=member;self.budget=budget;self.tail=b''
    def read(self,n=-1):
        raw=self.member.read(min(n if n>=0 else 65536,65536));self.budget[0]+=len(raw)
        if self.budget[0]>MAX_KML:raise ValueError('Documentos KML excedem o limite de XML descompactado.')
        scan=(self.tail+raw.replace(b'\x00',b'')).upper();self.tail=scan[-32:]
        if b'<!DOCTYPE' in scan or b'<!ENTITY' in scan:raise ValueError('KML com DTD/entidades não é aceito.')
        return raw


def placemarks(path,stats=None):
    """XML incremental: retém só um Placemark; anexos não são expandidos."""
    stats=stats if stats is not None else {};stats['kml_documents']=0
    try:
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist();names=[];size=0
            if len(infos)>MAX_FILES:raise ValueError('KMZ contém mais de 20.000 entradas. Divida o arquivo.')
            for info in infos:
                name=info.filename.replace('\\','/');parts=PurePosixPath(name).parts
                if name.startswith('/') or '..' in parts or re.match(r'^[A-Za-z]:',name) or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('KMZ contém caminho interno inseguro ou link simbólico.')
                if info.flag_bits&1:raise ValueError('KMZ protegido por senha. Exporte novamente sem criptografia.')
                if name.lower().endswith('.kml'):names.append(info);size+=info.file_size
            if not names:raise ValueError('KMZ não contém documento .kml.')
            if size>MAX_KML:raise ValueError(f'Os documentos KML internos somam {size/1048576:.1f} MB; limite de {MAX_KML/1048576:g} MB de XML. Divida a referência.')
            budget=[0]
            for info in names:
                stats['kml_documents']+=1;stack=[];inside=0
                with archive.open(info) as member:
                    for event,element in ET.iterparse(_LimitedXML(member,budget),events=('start','end')):
                        tag=element.tag.rsplit('}',1)[-1]
                        if event=='start':
                            if not stack and tag.lower()!='kml':raise ValueError('O XML interno não tem raiz KML válida.')
                            stack.append(element)
                            if len(stack)>128:raise ValueError('KML excede 128 níveis de elementos. Simplifique a estrutura.')
                            if tag=='Placemark':inside+=1
                        else:
                            if tag=='Placemark':
                                yield info.filename,element
                                inside-=1;element.clear()
                                if len(stack)>1:stack[-2].remove(element)
                            elif not inside:element.clear()
                            stack.pop()
            stats['xml_bytes']=budget[0]
    except zipfile.BadZipFile as exc:raise ValueError('KMZ corrompido ou não é ZIP válido. Exporte novamente no programa de origem.') from exc
    except ET.ParseError as exc:raise ValueError('Documento KML interno malformado: '+str(exc)[:180]) from exc
    except (RuntimeError,NotImplementedError) as exc:raise ValueError('Não foi possível ler a compressão / proteção do KMZ.') from exc


def validate(path):
    stats={}
    for _ in placemarks(path,stats):pass
    return {**stats,'kml_limit_mb':MAX_KML/1048576,'attachments_extracted':False,'method':'xml_incremental'}
