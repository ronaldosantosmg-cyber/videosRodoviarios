"""Histórico numérico em blocos imutáveis; somente dois blocos decodificados em RAM."""
from collections import OrderedDict
from pathlib import Path
import bisect
import hashlib
import os
import re
import uuid
import zipfile
import numpy as np

MAX_BLOCK_BYTES=128*1024*1024
MAX_FRAMES=500000
DTYPES=(np.dtype('int32'),np.dtype('float64'),np.dtype('int32'),np.dtype('int32'),np.dtype('float64'))


def _digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()


class FrameArchive:
    def __init__(self,root,create=True):
        self.root=Path(root).absolute()
        if self.root.is_symlink():raise ValueError('Histórico por link recusado.')
        if create:self.root.mkdir(parents=True,exist_ok=True)
        self.segments=[];self.length=0;self._pending=[];self._warning_pending=[]
        self._cache=OrderedDict();self._verified={}
        self.frames=FrameSequence(self);self.warnings=WarningSequence(self)

    def export_state(self):
        self.flush()
        return {'root':str(self.root.resolve()),'segments':[dict(row) for row in self.segments],'length':self.length}

    @classmethod
    def from_state(cls,state,base_directory=None):
        root=Path(state['root'])
        if not root.is_absolute() or root.is_symlink():raise ValueError('Pasta do histórico inválida.')
        if base_directory is not None:
            base=Path(base_directory).resolve()
            if not root.resolve().is_relative_to(base):raise ValueError('Histórico fora do cache.')
            cursor=root
            while cursor!=base and cursor!=cursor.parent:
                if cursor.is_symlink():raise ValueError('Link no histórico recusado.')
                cursor=cursor.parent
        obj=cls(root,create=False);rows=state['segments'];length=state['length']
        if not isinstance(length,int) or not 0<=length<=MAX_FRAMES or not isinstance(rows,list) or len(rows)>MAX_FRAMES:raise ValueError('Histórico extenso ou inválido.')
        cursor=0
        for row in rows:
            if not isinstance(row,dict) or row.get('start')!=cursor or not isinstance(row.get('count'),int) or not 1<=row['count']<=10000:raise ValueError('Blocos fora de sequência.')
            if not re.fullmatch(r'[0-9a-f]{32}\.npz',row.get('name','')) or not re.fullmatch(r'[0-9a-f]{64}',row.get('sha256','')):raise ValueError('Arquivo de histórico inválido.')
            obj.segments.append(dict(row));obj._validate(row);cursor+=row['count']
        if cursor!=length:raise ValueError('Histórico incompleto.')
        obj.length=length
        return obj

    def _validate(self,row):
        path=self.root/row['name']
        if path.is_symlink() or not path.is_file():raise ValueError('Bloco de histórico ausente.')
        stat=path.stat();stamp=(stat.st_size,stat.st_mtime_ns,stat.st_ino)
        if not 0<stat.st_size<=MAX_BLOCK_BYTES:raise ValueError('Bloco excede o limite.')
        if self._verified.get(row['name'])!=stamp:
            if _digest(path)!=row['sha256']:raise ValueError('Bloco de histórico alterado.')
            self._verified[row['name']]=stamp;self._cache.pop(row['name'],None)
        return path

    def flush(self):
        if not self._pending:return
        if len(self._pending)!=len(self._warning_pending):raise ValueError('Sinais e posições fora de sequência.')
        offsets=np.r_[0,np.cumsum([len(frame[0]) for frame in self._pending])].astype(np.int64)
        warning_offsets=np.r_[0,np.cumsum([len(values) for values in self._warning_pending])].astype(np.int64)
        arrays={str(i):np.concatenate([np.asarray(frame[i],dtype=DTYPES[i]) for frame in self._pending]) for i in range(5)}
        arrays.update(offsets=offsets,warning_offsets=warning_offsets,
                      warnings=np.asarray([v for values in self._warning_pending for v in sorted(values)],np.int64))
        if sum(a.nbytes for a in arrays.values())>MAX_BLOCK_BYTES:raise ValueError('Bloco de tráfego excede orçamento; reduza o tamanho do bloco.')
        name=uuid.uuid4().hex+'.npz';temporary=self.root/('.'+name)
        try:
            with temporary.open('wb') as stream:np.savez(stream,**arrays)
            os.replace(temporary,self.root/name)
        finally:temporary.unlink(missing_ok=True)
        self.segments.append({'name':name,'sha256':_digest(self.root/name),'start':self.length-len(self._pending),'count':len(self._pending)})
        self._pending.clear();self._warning_pending.clear()

    def _load(self,row):
        path=self._validate(row);name=row['name']
        if name in self._cache:self._cache.move_to_end(name);return self._cache[name]
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist()
            if len(infos)!=8 or sum(i.file_size for i in infos)>MAX_BLOCK_BYTES:raise ValueError('Arquivo de histórico excede orçamento.')
            # np.load não deve alocar um shape declarado maior que o conteúdo real.
            for info in infos:
                with archive.open(info) as stream:
                    version=np.lib.format.read_magic(stream)
                    if version==(1,0):shape,order,dtype=np.lib.format.read_array_header_1_0(stream)
                    elif version==(2,0):shape,order,dtype=np.lib.format.read_array_header_2_0(stream)
                    else:raise ValueError('Cabeçalho NPY não suportado.')
                    count=1
                    for size in shape:
                        if not isinstance(size,int) or size<0:raise ValueError('Shape inválido.')
                        count*=size
                    if dtype.hasobject or count*dtype.itemsize>MAX_BLOCK_BYTES or count*dtype.itemsize>info.file_size:raise ValueError('Matriz de histórico inválida.')
        with np.load(path,allow_pickle=False) as source:arrays={k:source[k] for k in source.files}
        if set(arrays)!={'0','1','2','3','4','offsets','warning_offsets','warnings'}:raise ValueError('Campos de histórico inválidos.')
        offsets=arrays['offsets'];wo=arrays['warning_offsets']
        if offsets.dtype!=np.int64 or wo.dtype!=np.int64 or offsets.shape!=(row['count']+1,) or wo.shape!=offsets.shape:raise ValueError('Índice inválido.')
        if offsets[0]!=0 or wo[0]!=0 or (np.diff(offsets)<0).any() or (np.diff(wo)<0).any():raise ValueError('Índice fora de ordem.')
        for i,dtype in enumerate(DTYPES):
            if arrays[str(i)].dtype!=dtype or arrays[str(i)].shape!=(int(offsets[-1]),):raise ValueError('Coluna de histórico inválida.')
        if arrays['warnings'].dtype!=np.int64 or arrays['warnings'].shape!=(int(wo[-1]),):raise ValueError('Sinais inválidos.')
        for value in arrays.values():value.flags.writeable=False
        self._cache[name]=arrays
        while len(self._cache)>2:self._cache.popitem(last=False)
        return arrays

    def get(self,index,warning=False):
        if index<0:index+=self.length
        if not 0<=index<self.length:raise IndexError(index)
        pending_start=self.length-len(self._pending)
        if index>=pending_start:
            return self._warning_pending[index-pending_start] if warning else self._pending[index-pending_start]
        starts=[row['start'] for row in self.segments];row=self.segments[bisect.bisect_right(starts,index)-1]
        arrays=self._load(row);local=index-row['start']
        if warning:
            a,b=arrays['warning_offsets'][local:local+2];return set(arrays['warnings'][a:b].tolist())
        a,b=arrays['offsets'][local:local+2];return tuple(arrays[str(i)][a:b] for i in range(5))

    def __getstate__(self):return self.export_state()
    def __setstate__(self,state):
        self.__dict__.update(self.from_state(state).__dict__)
        self.frames=FrameSequence(self);self.warnings=WarningSequence(self)


class FrameSequence:
    def __init__(self,archive):self.archive=archive
    def __len__(self):return self.archive.length
    def __getitem__(self,index):
        if isinstance(index,slice):return [self[i] for i in range(*index.indices(len(self)))]
        return self.archive.get(index)
    def append(self,frame):
        if len(frame)!=5 or len({len(a) for a in frame})!=1:raise ValueError('Estado veicular inválido.')
        self.archive._pending.append(frame);self.archive.length+=1
        if self.archive.length>MAX_FRAMES:raise ValueError('Histórico excede limite de quadros físicos.')


class WarningSequence(FrameSequence):
    def __getitem__(self,index):
        if isinstance(index,slice):return [self[i] for i in range(*index.indices(len(self)))]
        return self.archive.get(index,True)
    def append(self,value):self.archive._warning_pending.append(set(value))
