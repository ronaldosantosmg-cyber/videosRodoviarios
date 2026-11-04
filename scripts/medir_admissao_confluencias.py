"""Compara a proteção ligada/desligada em cenário sintético; não altera configurações salvas."""
import sys,time,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'suporte/sistema'),str(ROOT/'tests')]
from test_confluence_admission import simulator
from app.simulation import TrafficSim
from app.fleet_policy import require_export
original=TrafficSim.entry_confluence_ready;results=[]
for enabled in (False,True):
 TrafficSim.entry_confluence_ready=original if enabled else lambda *args:True
 for warmup in (0,10):
  times=[];rows=[]
  for rep in range(3):
   start=time.perf_counter();sim=simulator(traffic_density=4,traffic_seed=2,traffic_warmup_s=warmup);sim.run();elapsed=time.perf_counter()-start
   try:require_export(sim,sim.s);valid=True
   except ValueError:valid=False
   times.append(elapsed);rows.append({'valid':valid,'violations':sim.fleet_audit['violations'],'collisions':sim.collisions+sim.side_collisions,'exits':sum(sim.exited_by_path),'entered':sim.spawned,'gate':sim.report()['confluence_admission']})
  row={'enabled':enabled,'warmup_s':warmup,'duration_s':80,'seconds':times,'median_s':statistics.median(times),'runs':rows};results.append(row);print(json.dumps(row),flush=True)
TrafficSim.entry_confluence_ready=original
output=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'dist/admissao_confluencias.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(results,ensure_ascii=False,indent=2))
