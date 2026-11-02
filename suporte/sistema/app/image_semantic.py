"""Inferência ONNX local, sem downloads, execução de scripts ou envio da imagem.

O modelo precisa de pesos e avaliação identificados por SHA-256. Este adaptador
não transforma um modelo ainda não avaliado em reconhecimento validado.
"""
import hashlib,json,threading
from pathlib import Path
import cv2
import numpy as np
from .image_context_models import LABELS

_lock=threading.Lock()


def load_manifest(directory):
    root=Path(directory)
    manifest=root/'modelo.json';weights=root/'modelo.onnx'
    if root.is_symlink() or manifest.is_symlink() or weights.is_symlink():raise ValueError('Modelo semântico não pode usar links simbólicos.')
    if not manifest.is_file() or not weights.is_file():raise ValueError('Modelo semântico local não instalado. Use a análise assistida ou instale pesos e avaliação do modelo.')
    if manifest.stat().st_size>65536 or not 0<weights.stat().st_size<=128*1024*1024:raise ValueError('Modelo semântico excede os limites de tamanho.')
    config=json.loads(manifest.read_text(encoding='utf-8'))
    classes=config.get('classes',[])
    if not isinstance(classes,list) or not 2<=len(classes)<=32 or any(c not in LABELS for c in classes):raise ValueError('Classes do modelo incompatíveis.')
    if len(set(classes))!=len(classes):raise ValueError('Classes duplicadas no modelo.')
    if config.get('input_size') not in (256,512,1024):raise ValueError('Resolução do modelo incompatível.')
    if config.get('output') not in ('logits','probabilities'):raise ValueError('Formato de saída do modelo inválido.')
    digest=hashlib.sha256(weights.read_bytes()).hexdigest()
    if config.get('sha256')!=digest:raise ValueError('Integridade dos pesos do modelo semântico não confere.')
    mean=np.asarray(config.get('mean'),float);std=np.asarray(config.get('std'),float)
    if mean.shape!=(3,) or std.shape!=(3,) or not np.isfinite(mean).all() or not np.isfinite(std).all() or np.any(std<=0):raise ValueError('Normalização do modelo inválida.')
    threshold=float(config.get('confidence_threshold',.75))
    if not np.isfinite(threshold) or not .5<=threshold<=.99:raise ValueError('Confiança mínima inválida.')
    evaluation=config.get('evaluation',{})
    if evaluation.get('model_sha256')!=digest or not evaluation.get('dataset') or not evaluation.get('independent_holdout'):
        raise ValueError('Modelo sem avaliação independente identificada. Não é possível habilitar o reconhecimento.')
    metrics=evaluation.get('classes',{})
    for role in classes:
        if role=='unclassified':continue
        metric=metrics.get(role,{})
        count=metric.get('annotated_objects',0);iou=metric.get('iou',-1)
        if not isinstance(count,int) or count<20 or not isinstance(iou,(int,float)) or not np.isfinite(iou) or not .5<=iou<=1:
            raise ValueError(f'Avaliação insuficiente para a classe {LABELS[role]}.')
    return config,weights


def status(directory):
    try:
        config,_=load_manifest(directory)
        return dict(available=True,classes=config['classes'],model_sha256=config['sha256'],evaluation=config['evaluation'])
    except (ValueError,OSError,TypeError,KeyError) as exc:
        return dict(available=False,reason=str(exc))


def predict(rgb,directory,*,cancel=lambda:False):
    config,weights=load_manifest(directory);image=np.asarray(rgb)
    if image.dtype!=np.uint8 or image.ndim!=3 or image.shape[2] not in (3,4) or max(image.shape[:2])>2048 or min(image.shape[:2])<8:raise ValueError('Imagem inválida para reconhecimento.')
    if cancel():raise InterruptedError('Reconhecimento cancelado.')
    size=config['input_size'];mean=np.asarray(config['mean'],np.float32);std=np.asarray(config['std'],np.float32)
    resized=cv2.resize(image[:,:,:3],(size,size),interpolation=cv2.INTER_AREA).astype(np.float32)/255
    blob=np.ascontiguousarray(((resized-mean)/std).transpose(2,0,1)[None])
    # Uma rede por vez, CPU e dimensões limitadas; nenhum segundo motor gráfico.
    with _lock:
        if cancel():raise InterruptedError('Reconhecimento cancelado.')
        net=cv2.dnn.readNetFromONNX(str(weights));net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV);net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
        net.setInput(blob);output=np.asarray(net.forward(),np.float32)
    if cancel():raise InterruptedError('Reconhecimento cancelado.')
    if output.ndim!=4 or output.shape[0]!=1 or output.shape[1]!=len(config['classes']) or max(output.shape[2:])>1024 or not np.isfinite(output).all():raise ValueError('Saída do modelo semântico inválida.')
    scores=output[0]
    if config['output']=='logits':
        scores=np.exp(scores-scores.max(axis=0,keepdims=True));scores/=scores.sum(axis=0,keepdims=True)
    elif np.any(scores<0) or np.any(scores>1) or not np.allclose(scores.sum(axis=0),1,atol=.02):raise ValueError('Probabilidades semânticas inválidas.')
    best=scores.argmax(axis=0).astype(np.int16);confidence=scores.max(axis=0)
    best[confidence<config.get('confidence_threshold',.75)]=-1
    h,w=image.shape[:2];best=cv2.resize(best,(w,h),interpolation=cv2.INTER_NEAREST)
    confidence=cv2.resize(confidence,(w,h),interpolation=cv2.INTER_LINEAR)
    if image.shape[2]==4:best[image[:,:,3]==0]=-1
    return dict(labels=best,confidence=confidence,classes=config['classes'],model_sha256=config['sha256'],evaluation=config['evaluation'])
