"""1.42.43: cálculos de tempo de semáforo e de pare e siga (funções puras, sem dependências).

Fórmulas usuais de engenharia de tráfego (ITE/CONTRAN, valores de projeto adotáveis):
- amarelo = tempo de percepção/reação + v / (2·desaceleração), entre 3 e 6 s;
- vermelho geral = (largura a limpar + comprimento do veículo) / v;
- verde de pedestres = 7 s de partida + travessia / 1,2 m/s;
- escoamento de fila: perda de partida + n × intervalo entre veículos.
"""
import math

REACTION_S=1.0
DECEL_MPS2=3.0
WALK_SPEED_MPS=1.2
WALK_START_S=7.0
STARTUP_LOST_S=2.0
HEADWAY_S=2.0
VEHICLE_LENGTH_M=6.0

def amber_s(speed_mps,decel=DECEL_MPS2,reaction=REACTION_S):
    v=max(0.,float(speed_mps));return min(6.,max(3.,reaction+v/(2*decel)))

def all_red_s(clear_width_m,speed_mps,vehicle_length_m=VEHICLE_LENGTH_M):
    v=max(1.,float(speed_mps));return min(12.,max(1.,(max(0.,float(clear_width_m))+vehicle_length_m)/v))

def pedestrian_walk_s(crossing_m,walk_speed=WALK_SPEED_MPS,start=WALK_START_S):
    return start+max(0.,float(crossing_m))/walk_speed

def queue_discharge_s(n,startup=STARTUP_LOST_S,headway=HEADWAY_S):
    return 0. if n<=0 else startup+n*headway

def zone_clearance_s(zone_length_m,speed_mps,vehicle_length_m=VEHICLE_LENGTH_M):
    """Tempo para o último veículo que entrou deixar o trecho em pare e siga."""
    return (max(0.,float(zone_length_m))+vehicle_length_m)/max(1.,float(speed_mps))

def alternating_switch(elapsed_s,min_s,max_s,current_demand,opposite_demand):
    """Pare e siga inteligente: verde mínimo, prolongamento enquanto há fila no sentido liberado,
    encerramento ao esvaziar (gap-out) ou no máximo; nunca troca sem demanda contrária."""
    if elapsed_s<min_s-1e-9:return False
    if opposite_demand<=0:return False
    if current_demand<=0:return True
    return elapsed_s>=max_s-1e-9

def audit_signal(*,speed_kmh,amber_given_s,all_red_given_s,clear_span_m,walk_given_s,crossing_m,phases):
    """Compara o que o semáforo tem com o que a geometria e a velocidade exigem. Devolve avisos em português."""
    v=speed_kmh/3.6;need_amber=amber_s(v);need_red=all_red_s(clear_span_m,v);need_walk=pedestrian_walk_s(crossing_m)
    warnings=[]
    if amber_given_s+1e-9<need_amber:warnings.append(f'Amarelo de {amber_given_s:.1f} s é menor que o necessário ({need_amber:.1f} s) a {speed_kmh:.0f} km/h.')
    if all_red_given_s+1e-9<need_red:warnings.append(f'Vermelho geral de {all_red_given_s:.1f} s é menor que o necessário para limpar o cruzamento ({need_red:.1f} s).')
    if phases==3 and walk_given_s+1e-9<need_walk:warnings.append(f'Verde de pedestres de {walk_given_s:.1f} s não cobre a travessia de {crossing_m:.1f} m ({need_walk:.1f} s necessários).')
    return {'amber_required_s':round(need_amber,1),'all_red_required_s':round(need_red,1),'walk_required_s':round(need_walk,1) if phases==3 else None,'warnings':warnings}

MAX_STOP_DECEL_MPS2=4.5

def can_stop(speed_mps,gap_m,max_decel=MAX_STOP_DECEL_MPS2):
    """Zona de dilema: no amarelo, quem não consegue parar antes da linha com frenagem aceitável segue em frente."""
    v=max(0.,float(speed_mps));return v*v/(2*max_decel)<=max(0.,float(gap_m))+1e-9
