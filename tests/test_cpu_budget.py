from app.encoding import cpu_threads
from app.parallel import plan_workers


def test_montagem_e_encoder_compartilham_orcamento():
    for cores in (4, 8, 16, 32):
        workers, _ = plan_workers(0, 1280, 720, 1000, True, cores=cores, memory=64 * 1024**3)
        assert workers + cpu_threads(cores) <= cores - 1
    assert cpu_threads(1) == 1
    assert plan_workers(0, 1280, 720, 1000, True, cores=2, memory=8 * 1024**3)[0] == 1
