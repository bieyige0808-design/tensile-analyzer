"""Generate reproducible, nonexperimental example files."""
from pathlib import Path
import csv
import numpy as np

def generate(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(42)
    for name,modulus in [('Synthetic_A',5000),('Synthetic_B',8000)]:
        groups=[]
        for trial in range(3):
            t=np.arange(0,2.01,.01);strain=t*.01
            break_at=.014+trial*.001
            stress=modulus*(1+trial*.03)*strain+rng.normal(0,.03,len(t))
            stress[strain>break_at]=.01
            groups.append((t,stress*4*.01,strain*20))
        with (destination/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.writer(f);writer.writerow([v for i in range(3) for v in (f'Trial_{i+1}','','')])
            writer.writerow(['Time','Force','Stroke']*3);writer.writerow(['s','N','mm']*3)
            for i in range(len(groups[0][0])):writer.writerow([a[i] for group in groups for a in group])

if __name__=='__main__':generate(Path(__file__).parent/'synthetic_data')
