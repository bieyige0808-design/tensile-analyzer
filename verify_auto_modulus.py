"""Known piecewise slope and automatic fit/origin checks."""
from pathlib import Path
import tempfile
import tkinter as tk
import numpy as np
from openpyxl import load_workbook
import tensile_core as core
from tensile_gui import App

x=np.arange(0,.01501,.00005);t=np.arange(len(x))*.01
y=1000*x+9000*np.clip(x-.004,0,.004)
raw=np.column_stack((t,y*.04,x*20))
r=core.analyze_trial(raw,4,.01,20,auto_fit=True)
assert abs(r['modulus']-10)<1e-7
assert abs(r['fit_min']-.4)<1e-7
assert abs(r['fit_max']-.6)<1e-7
assert abs(r['plot_origin']-.36)<1e-7
assert abs(r['intercept']-r['modulus']*1000*r['plot_shift']/100)<1e-7
root=tk.Tk();root.withdraw();app=App(root)
p=next((Path(__file__).parent/'examples/synthetic_data').glob('*.csv'));app.add([p])
data=next(iter(app.items.values()));data['thickness'].set('.01');app.draw_preview()
for result,label in zip(data['results'],data['labels']):
    assert abs(result['fit_max']-result['fit_min']-.2)<1e-10
    assert abs(float(data['options'][label]['fit_lo'].get())-result['fit_min'])<1e-7
    assert abs(float(data['options'][label]['shift'].get())+result['plot_origin'])<1e-7
index=data['choices'].index(data['trial'].get())
assert abs(float(data['fit_lo'].get())-data['results'][index]['fit_min'])<1e-7
with tempfile.TemporaryDirectory() as folder:
    out=Path(folder)/'auto.xlsx';configs,_=app.export_configs();results=core.process_files(configs,out,emit=lambda _:None)
    wb=load_workbook(out);res=results[p.stem][0][1]
    assert abs(wb['Trial_000']['X5'].value-(wb['Trial_000']['S5'].value+res['plot_shift']))<1e-9
    assert abs(wb['Summary']['P2'].value-res['plot_origin'])<1e-9
root.destroy();print('Maximum modulus, zero-stress intercept and actual plot-shift autofill verified')
