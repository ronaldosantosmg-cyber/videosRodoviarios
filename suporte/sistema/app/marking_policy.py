"""Defesa semântica: tinta de sinalização nunca cria um obstáculo físico."""
import re,unicodedata
from .zebrados import named_layer


def paint_only_layer(layer):
    name=''.join(c for c in unicodedata.normalize('NFKD',str(layer).upper()) if not unicodedata.combining(c))
    if named_layer(layer):return True
    if re.search(r'(^|[^A-Z0-9])(SETAS?|ZEBRADOS?|SECCIONAD[AO]S?|TRACEJAD[AO]S?|DASHED)([^A-Z0-9]|$)',name):return True
    match=re.search(r'(^|[^A-Z])SH[_ -]([A-Z]+)',name)
    # LBO é bordo. As demais pinturas SH são apresentação/regulação, não paredes.
    return bool(match and match.group(2)!='LBO')


def nonblocking(entity):
    return entity.get('role') in ('sign_h','axis') or paint_only_layer(entity.get('layer',''))
