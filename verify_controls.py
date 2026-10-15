"""Check partial export, additive plot shifts, repeat buttons and clearing."""
from pathlib import Path
import tempfile
import tkinter as tk
from openpyxl import load_workbook
from tensile_gui import App
import tensile_core as core

root=tk.Tk();root.withdraw();app=App(root)
files=sorted((Path(__file__).parent/'examples/synthetic_data').glob('*.csv'))
app.add(files);first,second=app.items.values();first['thickness'].set('.01')
configs,skipped=app.export_configs()
assert len(configs)==1 and skipped==[files[1].stem]
first['sample_shift'].set('.1');first['options'][first['labels'][0]]['shift'].set('.02')
assert abs(app.trial_options(first)[first['labels'][0]]['plot_shift']-.12)<1e-9
buttons=[w for w in first['widgets'][-1].winfo_children() if isinstance(w,tk.Button)]
buttons[1].invoke();assert first['sample_shift'].get()=='.11' or first['sample_shift'].get()=='0.11'
buttons[0].invoke();assert first['sample_shift'].get()=='0.10'
assert int(buttons[0].cget('repeatinterval'))==65
app.draw_preview();first['trial'].set(first['choices'][0]);first['sample_shift'].set('.2');app.draw_preview()
assert first['trial'].get()==first['choices'][0]
with tempfile.TemporaryDirectory() as folder:
    output=Path(folder)/'controls.xlsx';configs,_=app.export_configs();core.process_files(configs,output,emit=lambda _:None)
    wb=load_workbook(output)
    assert wb['Properties']._charts[0].legend is None
    assert wb['Stress_Strain']._charts[0].legend.position=='t'
    assert len(wb['Summary']['A'])==6
app.details(str(files[0].resolve()));window=first['detail'].window
assert first['detail'].canvas.cget('yscrollcommand')
assert first['detail'].rows.bind('<MouseWheel>')
app.clear_imports();assert not app.items and not app.tree.get_children() and not window.winfo_exists()
root.destroy();print('Partial export, repeat controls, shifts, legends and clearing verified')
