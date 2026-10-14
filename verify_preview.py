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
assert 'Trial 2' in app.preview_title.get()
app.params['Gauge length (mm)'].set('30');app.draw_preview()
app.select_sample(second);app.draw_preview()
assert '0.02' in app.preview_note.get()
app.items[second]['thickness'].set('');app.draw_preview()
assert len(app.plot.find_all())==1
root.destroy()
print('Import, individual thickness, trial switch and preview checks passed')
