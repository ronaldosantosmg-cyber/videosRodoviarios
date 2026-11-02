import time
from app.progress_pulse import Pulse,stop_all


def test_pulse_advances_and_stops():
    seen=[]
    p=Pulse(lambda a,b:seen.append((a,b)),lambda:False,.26,.92,period=.05);p.start('Teste')
    time.sleep(.3);p.stop();n=len(seen);time.sleep(.2)
    assert n>=3 and len(seen)==n
    assert all(.26<=a<.92 for a,_ in seen) and seen[-1][0]>seen[0][0]


def test_pulse_survives_status_errors():
    def bad(a,b):raise InterruptedError('x')
    p=Pulse(bad,lambda:False,.2,.9,period=.02);p.start('x');time.sleep(.1);stop_all()
