"""Check per-trial edits, exclusion and exported chart geometry."""
from pathlib import Path
import tempfile
import tkinter as tk
import numpy as np
from openpyxl import load_workbook
from tensile_gui import App
import tensile_core as core

root=tk.Tk();root.withdraw();app=App(root)
p=next((Path(__file__).parent/'examples/synthetic_data').glob('*.csv'))
app.add([p]);data=next(iter(app.items.values()));data['thickness'].set('.01');app.draw_preview()
label=data['labels'][0];opts=data['options'][label]
old=data['results'][0]['strength'];opts['thickness'].set('.02');opts['fit_lo'].set('.1');opts['fit_hi'].set('.3')
opts['included'].set(False);app.draw_preview()
assert abs(data['results'][0]['strength']-old/2)<1e-8
expected=np.mean([r['strength'] for r in data['results'][1:]])
assert abs(float(data['stats'][0].get())-expected)<.05
app.details(str(p.resolve()));detail=data['detail'];detail.refresh()
assert detail.result_vars[0][4].get().endswith('excluded')
detail.window.destroy();app.details(str(p.resolve()))
assert data['options'][label]['thickness'].get()=='.02'
with tempfile.TemporaryDirectory() as d:
    output=Path(d)/'analysis.xlsx'
    configs=[(p,4,.01,20,{},.05,.25,app.trial_options(data))]
    results=core.process_files(configs,output,emit=lambda _:None)
    assert not results[p.stem][0][1]['included']
    assert results[p.stem][0][1]['fit_min']==.1
    wb=load_workbook(output)
    assert wb['Summary']['N2'].value=='No'
    assert abs(wb['Properties']['Q2'].value-expected)<1e-8
    chart=wb['Properties']._charts[0]
    assert chart.layout.manualLayout.w==.8 and chart.layout.manualLayout.h==.8
    assert chart.y_axis.delete is False
    assert chart._charts[1].y_axis.axPos=='r'
    assert chart._charts[1].y_axis.crossAx==10
root.destroy()
print('Trial overrides, exclusion, persistence, export and chart layout verified')
