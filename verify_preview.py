"""Exercise import, per-sample dimensions and trial switching in Tk."""
from pathlib import Path
import tkinter as tk
from tensile_gui import App

root=tk.Tk();root.withdraw();app=App(root)
files=sorted((Path(__file__).parent/'examples'/'synthetic_data').glob('*.csv'))
app.add(files)
assert len(app.items)==2
first=str(files[0].resolve());second=str(files[1].resolve())
app.items[first]['thickness'].set('0.01');app.items[second]['thickness'].set('0.02')
assert app.items[first]['thickness'].get()=='0.01'
app.select_sample(first);app.draw_preview()
assert len(app.plot.find_all())>20
app.items[first]['trial'].set(app.items[first]['choices'][1]);app.draw_preview()
assert len(app.plot.find_withtag('sample_curve'))==2
app.items[first]['fit_lo'].set('0.10');app.items[first]['fit_hi'].set('0.30');app.draw_preview()
assert app.items[first]['cache_key'][3:5]==(.10,.30)
assert len(app.plot.find_withtag('fit_range'))==2
app.params['Gauge length (mm)'].set('30');app.draw_preview()
app.select_sample(second);app.draw_preview()
assert app.items[second]['stats'][0].get()!='—'
app.items[second]['thickness'].set('');app.draw_preview()
assert len(app.plot.find_withtag('sample_curve'))==1
assert int(app.samples_canvas.cget('height'))==190
root.destroy()
print('Import, individual thickness, trial switch and preview checks passed')
