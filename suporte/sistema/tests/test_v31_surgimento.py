import numpy as np
from app import surgimento as sg, relevo


def test_peso_decai_atras_da_frente_e_zera_alem():
    w = sg.peso([0, 80, 100, 120], 100.)
    assert w[0] == 0 and 0 < w[1] < 1 and w[2] == 1 and w[3] == 0


def test_halo_nao_quebra_nas_bordas_nem_com_peso_zero():
    im = np.zeros((20, 20, 3), np.uint8)
    sg.halo(None, im, -30, -30, 5, 1.)
    sg.halo(None, im, 10, 10, 5, 0.)
    sg.halo(None, im, 10, 10, 5, 1.)
    assert im[10, 10].sum() > 0


def test_taludes_mantem_matiz_e_ganham_granulometria():
    X, Y = np.meshgrid(np.arange(64) * .05, np.arange(64) * .05)
    for role, base in (('cut', (224, 83, 69)), ('fill', (56, 183, 93))):
        c = np.broadcast_to(np.array(base, float), (64, 64, 3)).copy()
        out = relevo.MATERIAIS[role](c, X, Y, .05, 7)
        assert out.shape == c.shape and np.isfinite(out).all() and out.std() > 0
        assert np.argmax(out.mean((0, 1))) == np.argmax(base)


def test_asfalto_existente_mais_chapado_que_o_novo_nao_e_mais_rugoso():
    X, Y = np.meshgrid(np.arange(96) * .02, np.arange(96) * .02)
    c = np.full((96, 96, 3), 120., float)
    ex = relevo._asfalto_exist(c, X, Y, .02, 3)
    nv = relevo._asfalto_novo(c, X, Y, .02, 3)
    rug = lambda a: np.abs(np.diff(a[..., 0], axis=1)).mean()
    assert np.isfinite(ex).all() and rug(ex) < .6 * rug(nv)
