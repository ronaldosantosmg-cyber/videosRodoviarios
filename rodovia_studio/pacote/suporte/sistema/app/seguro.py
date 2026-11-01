"""2.29: aritmética protegida. Divisão por zero, NaN/infinito e entradas vazias viram resultado definido, nunca erro nem lixo.

Regras: para entradas normais o resultado é idêntico ao da operação comum; só os casos degenerados mudam.
Todas as funções aceitam números e arrays do numpy.
"""
import math
import numpy as np

EPS=1e-12

def finito(x):
    """True se x (número ou array) não tem NaN nem infinito."""
    try:return bool(np.all(np.isfinite(np.asarray(x,dtype=float))))
    except (TypeError,ValueError):return False

def sdiv(a,b,padrao=0.0,eps=0.0):
    """a/b com proteção: denominador zero, quase zero (|b|<=eps) ou não finito devolve `padrao`; resultado não finito também."""
    if np.ndim(a)==0 and np.ndim(b)==0:
        try:
            a=float(a);b=float(b)
        except (TypeError,ValueError):return padrao
        if not math.isfinite(b) or abs(b)<=eps or b==0:return padrao
        r=a/b
        return r if math.isfinite(r) else padrao
    # preserva o tipo de ponto flutuante das entradas (ex.: float32 exigido pelo OpenCV); inteiros e escalares viram float64
    dts=[x.dtype for x in (a,b) if isinstance(x,np.ndarray) and np.issubdtype(x.dtype,np.floating)]
    dtype=np.result_type(*dts) if dts else np.float64
    A=np.asarray(a,dtype=dtype);B=np.asarray(b,dtype=dtype)
    shape=np.broadcast(A,B).shape;ok=np.isfinite(B)&(np.abs(B)>eps)&(B!=0)
    out=np.full(shape,padrao,dtype=dtype);np.divide(A,B,out=out,where=ok&np.ones(shape,bool))
    out[~np.isfinite(out)]=padrao
    return out

def limitar(x,lo,hi):
    """Limita x ao intervalo [lo, hi]; NaN vira lo."""
    if np.ndim(x)==0:
        try:x=float(x)
        except (TypeError,ValueError):return lo
        if math.isnan(x):return lo
        return min(max(x,lo),hi)
    x=np.nan_to_num(np.asarray(x,dtype=float),nan=lo,posinf=hi,neginf=lo);return np.clip(x,lo,hi)

def numero(x,padrao=0.0,lo=None,hi=None):
    """Converte para float finito; vazio, texto inválido, NaN e infinito viram `padrao`. Opcionalmente limita."""
    try:v=float(x)
    except (TypeError,ValueError):return padrao
    if not math.isfinite(v):return padrao
    if lo is not None:v=max(v,lo)
    if hi is not None:v=min(v,hi)
    return v

def exigir(valor,nome,vazio_ok=False):
    """Entrada obrigatória: None, texto vazio e coleção vazia levantam ValueError com mensagem clara (em português)."""
    vazio=valor is None or (isinstance(valor,str) and not valor.strip()) or (hasattr(valor,'__len__') and len(valor)==0)
    if vazio and not vazio_ok:raise ValueError(f'{nome}: informe um valor (a entrada está vazia).')
    return valor

def media(x,padrao=0.0):
    a=np.asarray(x,dtype=float).ravel();a=a[np.isfinite(a)]
    return float(a.mean()) if a.size else padrao
def minimo(x,padrao=0.0):
    a=np.asarray(x,dtype=float).ravel();a=a[np.isfinite(a)];return float(a.min()) if a.size else padrao
def maximo(x,padrao=0.0):
    a=np.asarray(x,dtype=float).ravel();a=a[np.isfinite(a)];return float(a.max()) if a.size else padrao
def desvio(x,padrao=0.0):
    a=np.asarray(x,dtype=float).ravel();a=a[np.isfinite(a)];return float(a.std()) if a.size>1 else padrao

def norma(v,eixo=-1):
    """Norma euclidiana protegida: não finitos viram 0."""
    return np.linalg.norm(np.nan_to_num(np.asarray(v,dtype=float),nan=0.,posinf=0.,neginf=0.),axis=eixo)

def unitario(v,padrao=None):
    """Vetor(es) de comprimento 1. Vetor nulo devolve `padrao` (zeros por omissão), sem dividir por zero."""
    a=np.nan_to_num(np.asarray(v,dtype=float),nan=0.,posinf=0.,neginf=0.);n=np.linalg.norm(a,axis=-1,keepdims=True)
    out=np.divide(a,n,out=np.zeros_like(a),where=n>EPS)
    if padrao is not None:
        nulo=(n<=EPS)[...,0];out=np.where(nulo[...,None],np.asarray(padrao,dtype=float),out)
    return out

def raiz(x,padrao=0.0):
    x=numero(x,padrao) if np.ndim(x)==0 else x
    if np.ndim(x)==0:return math.sqrt(x) if x>=0 else padrao
    a=np.asarray(x,dtype=float);return np.where(a>=0,np.sqrt(np.where(a>=0,a,0)),padrao)

def logaritmo(x,padrao=0.0):
    if np.ndim(x)==0:
        x=numero(x,float('nan'));return math.log(x) if x>0 else padrao
    a=np.asarray(x,dtype=float);return np.where(a>0,np.log(np.where(a>0,a,1)),padrao)

def validar_resultado(valor,nome='resultado'):
    """Falha cedo e em português quando um cálculo termina com NaN ou infinito, em vez de propagar o lixo."""
    if not finito(valor):raise ValueError(f'{nome}: o cálculo resultou em valor indefinido ou infinito. Confira as entradas (zeros, vazios ou unidades).')
    return valor
