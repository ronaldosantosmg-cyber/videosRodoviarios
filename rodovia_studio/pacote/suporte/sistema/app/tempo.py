"""1.33: tempos legíveis — até 60 s em segundos; acima, em minutos (e horas acima de 60 min)."""
def tempo(s):
    try:s=float(s)
    except (TypeError,ValueError):return str(s)
    if s!=s:return '—'
    s=max(0,int(round(s)))
    if s<60:return f'{s} s'
    if s<3600:
        m,r=divmod(s,60);return f'{m} min {r:02d} s' if r else f'{m} min'
    h,r=divmod(s,3600);m=r//60
    return f'{h} h {m:02d} min' if m else f'{h} h'
