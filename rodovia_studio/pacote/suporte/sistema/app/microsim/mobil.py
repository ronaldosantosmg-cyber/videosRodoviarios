"""MOBIL: segurança (mandatória) + incentivo. As acelerações vêm do motor (IDM) — este módulo só decide."""
from dataclasses import dataclass
from .params import MobilParams


@dataclass
class MobilResult:
    safe:bool
    incentive:float
    ok:bool


def evaluate(m:MobilParams,*,a_self,a_self_new,a_new_follower_after,a_new_follower_before,a_old_follower_after,a_old_follower_before,
             gap_front_ok=True,gap_rear_ok=True,toward_right=False,mandatory=False,b_safe=None):
    """Critério de segurança: ã_novo_seguidor >= -b_safe (e o próprio veículo também não pode frear além de b_safe).
    Incentivo: (a'-a)+p[(ã'_seg-ã_seg)+(ã'_novo-ã_novo)] + viés > a_th. Merge obrigatório dispensa o incentivo."""
    bs=m.b_safe if b_safe is None else b_safe
    safe=gap_front_ok and gap_rear_ok and a_new_follower_after>=-bs and a_self_new>=-bs
    gain=(a_self_new-a_self)+m.politeness*((a_old_follower_after-a_old_follower_before)+(a_new_follower_after-a_new_follower_before))
    gain+=m.bias_right if toward_right else -m.bias_right
    return MobilResult(safe,gain,safe and (mandatory or gain>m.a_th))
