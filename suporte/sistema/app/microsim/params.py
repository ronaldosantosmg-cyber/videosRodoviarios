"""Parâmetros do micro-simulador. Os limites de segurança são impostos aqui (não dependem do chamador)."""
from dataclasses import dataclass,field

S0_MIN=2.0      # m   distância mínima de parada
T_MIN=1.2       # s   tempo de reação seguro
T_PREP_MIN=1.0  # s   antecedência mínima da seta


@dataclass
class IDMParams:
    a_max:float=1.5      # m/s²  aceleração máxima confortável
    b:float=2.0          # m/s²  desaceleração confortável
    s0:float=2.0         # m     distância mínima (>= 2.0)
    T:float=1.2          # s     intervalo de tempo desejado (>= 1.2)
    delta:float=4.0
    b_max:float=9.0      # m/s²  limite físico da frenagem de emergência
    ttc_crit:float=1.5   # s     abaixo disso a frenagem passa a ser cinemática (hard braking)

    def __post_init__(self):
        self.s0=max(float(self.s0),S0_MIN);self.T=max(float(self.T),T_MIN)
        self.a_max=max(float(self.a_max),.1);self.b=max(float(self.b),.1);self.b_max=max(float(self.b_max),self.b)


@dataclass
class MobilParams:
    politeness:float=.2          # p
    b_safe:float=3.0             # m/s²  desaceleração máxima imposta ao novo seguidor
    a_th:float=.2                # m/s²  limiar de conveniência
    bias_right:float=0.          # m/s²  >0 favorece a faixa da direita
    t_prep:float=1.5             # s     seta antes de iniciar o movimento lateral (>= 1.0)
    t_change_min:float=3.0       # s     duração mínima da transição
    v_lat_max:float=1.2          # m/s   velocidade lateral de pico admitida
    return_gap_time:float=1.5    # s     folga (em tempo) sobre o ultrapassado antes de voltar
    return_gap_min:float=10.0    # m

    def __post_init__(self):
        self.t_prep=max(float(self.t_prep),T_PREP_MIN);self.b_safe=max(float(self.b_safe),.5)


@dataclass
class VehicleParams:
    length:float=4.5
    width:float=1.8
    v0_factor:float=1.0          # multiplica a velocidade desejada da faixa
    idm:IDMParams=field(default_factory=IDMParams)
    mobil:MobilParams=field(default_factory=MobilParams)


@dataclass
class EngineParams:
    dt:float=.1
    decision_interval:float=.5   # s entre decisões laterais de cada veículo
    cell:float=15.               # m  célula da grelha espacial
    clearance:float=.30          # m  folga mínima entre caixas (abaixo disso: congela o de trás)
    yield_margin:float=.80       # m  folga lateral abaixo da qual o de trás cede
    horizon:float=250.           # m  alcance da busca por líder
    closure_d_min:float=30.      # m  antecipação mínima do merge antes de uma interdição
    closure_t_ant:float=7.       # s  antecipação proporcional à velocidade
    lc_cooldown:float=5.         # s  intervalo mínimo entre trocas
    prep_timeout:float=8.        # s  desiste de uma troca discricionária sem brecha
    courtesy:bool=True           # o seguidor da faixa de destino abre espaço para um merge obrigatório
