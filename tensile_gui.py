"""Desktop interface for Tensile Analyzer."""
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from tkinter.scrolledtext import ScrolledText
import threading,queue,sys,os,subprocess
import tensile_core as core
import math
import numpy as np

class App:
    def __init__(self,root):
        self.root=root; self.items={}; self.events=queue.Queue(); self.running=False
        self.active=None; self.preview_job=None
        root.title('Tensile Analyzer 1.1'); root.geometry('1100x950')
        root.protocol('WM_DELETE_WINDOW',self.close)
        frame=ttk.Frame(root,padding=15); frame.pack(fill='both',expand=True)
        top=ttk.Frame(frame); top.pack(fill='x')
        for text,command in [('Select files',self.files),('Select folder',self.folder),('Remove selected',self.remove)]: ttk.Button(top,text=text,command=command).pack(side='left',padx=3)
        self.params={}
        settings=ttk.LabelFrame(frame,text='Defaults and analysis settings',padding=8); settings.pack(fill='x',pady=8)
        fields=[('Width (mm)','4'),('Gauge length (mm)','20'),('Fit min (%)','0.05'),('Fit max (%)','0.25'),('Drop (%)','50')]
        for i,(name,value) in enumerate(fields):
            var=tk.StringVar(value=value); self.params[name]=var
            ttk.Label(settings,text=name).grid(row=0,column=i,padx=5)
            ttk.Entry(settings,textvariable=var,width=12).grid(row=1,column=i,padx=5)
            var.trace_add('write',self.schedule_preview)
        self.smooth=tk.BooleanVar(value=False)
        ttk.Checkbutton(settings,text='Smooth plots only (Savitzky-Golay, 11 points)',variable=self.smooth,command=self.schedule_preview).grid(row=2,column=3,columnspan=2)
        self.tree=ttk.Treeview(frame,columns=('name','width','thickness','length','trials'),show='headings',height=7,selectmode='extended')
        for col,title in [('name','Sample'),('width','Width (mm)'),('thickness','Thickness (mm)'),('length','Gauge length (mm)'),('trials','Trials')]: self.tree.heading(col,text=title); self.tree.column(col,width=160)
        # Keep the old tree as internal state for manual fracture and export.
        self.sample_rows=ttk.Frame(frame); self.sample_rows.pack(fill='x')
        self.sample_rows.columnconfigure(0,weight=1)
        for col,title in enumerate(['Sample','Thickness (mm)','Trial number','']):ttk.Label(self.sample_rows,text=title).grid(row=0,column=col,padx=8,sticky='w')
        preview=ttk.LabelFrame(frame,text='Stress-strain preview',padding=6);preview.pack(fill='both',expand=True,pady=8)
        self.preview_title=tk.StringVar(value='Import CSV files or a folder')
        ttk.Label(preview,textvariable=self.preview_title).pack(anchor='w')
        self.plot=tk.Canvas(preview,bg='white',highlightthickness=0,height=300);self.plot.pack(fill='both',expand=True)
        self.plot.bind('<Configure>',self.schedule_preview)
        self.preview_note=tk.StringVar(value='Enter a sample thickness to display stress-strain data.')
        ttk.Label(preview,textvariable=self.preview_note).pack(anchor='w')
        out=ttk.Frame(frame); out.pack(fill='x',pady=6)
        self.save=tk.StringVar(value=str(Path.home()/'Desktop'))
        ttk.Label(out,text='Save folder').pack(side='left'); ttk.Entry(out,textvariable=self.save).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(out,text='Browse',command=self.save_folder).pack(side='left')
        controls=ttk.Frame(frame); controls.pack(fill='x')
        self.run_button=ttk.Button(controls,text='Run analysis',command=self.start); self.run_button.pack(side='left')
        ttk.Button(controls,text='Set manual fracture points',command=self.manual).pack(side='left',padx=8)
        self.status=tk.StringVar(value='Ready'); ttk.Label(controls,textvariable=self.status).pack(side='left')
        self.log=ScrolledText(frame,height=4,state='disabled'); self.log.pack(fill='x',pady=8)
        ttk.Label(frame,text='Engineering stress = force / area. Strain uses instrument stroke / gauge length. No zero/preload correction.\nFracture: >= selected drop within 0.1 s, confirmed by 3-5 subsequent points. Missing fracture results remain blank.').pack(anchor='w')
        root.after(100,self.poll)
    def add(self,paths):
        if self.running: return
        for p in paths:
            p=str(Path(p).resolve())
            if p in self.items: continue
            try:
                trials=core.read_trials(p); labels=[label for label,_ in trials]
            except Exception as e: messagebox.showerror('Invalid CSV',f'{Path(p).name}: {e}'); continue
            iid=self.tree.insert('', 'end',values=(Path(p).stem,self.params['Width (mm)'].get(),'',self.params['Gauge length (mm)'].get(),len(labels)))
            row=len(self.items)+1; thickness=tk.StringVar(value=''); trial=tk.StringVar(value=f'1: {labels[0]}')
            choices=[f'{i+1}: {label}' for i,label in enumerate(labels)]
            widgets=[ttk.Label(self.sample_rows,text=Path(p).stem),ttk.Entry(self.sample_rows,textvariable=thickness,width=14),
                ttk.Combobox(self.sample_rows,textvariable=trial,values=choices,state='readonly',width=24),
                ttk.Button(self.sample_rows,text='Preview',command=lambda p=p:self.select_sample(p))]
            for col,widget in enumerate(widgets):widget.grid(row=row,column=col,padx=8,pady=5,sticky='ew')
            self.items[p]={'iid':iid,'labels':labels,'overrides':{},'thickness':thickness,'trial':trial,'choices':choices,'trials':trials,'widgets':widgets}
            thickness.trace_add('write',lambda *args,p=p:self.select_sample(p))
            widgets[1].bind('<FocusIn>',lambda e,p=p:self.select_sample(p))
            widgets[2].bind('<<ComboboxSelected>>',lambda e,p=p:self.select_sample(p))
            self.select_sample(p)
    def files(self): self.add(filedialog.askopenfilenames(filetypes=[('CSV files','*.csv')]))
    def folder(self):
        p=filedialog.askdirectory()
        if p: self.add(sorted(x for x in Path(p).iterdir() if x.is_file() and x.suffix.lower()=='.csv'))
    def remove(self):
        if self.running:return
        for iid in self.tree.selection():
            for data in self.items.values():
                if data['iid']==iid:
                    for widget in data['widgets']:widget.destroy()
            self.tree.delete(iid)
            self.items={p:v for p,v in self.items.items() if v['iid']!=iid}
        for row,data in enumerate(self.items.values(),1):
            for widget in data['widgets']:widget.grid_configure(row=row)
        self.active=next(iter(self.items),None);self.schedule_preview()
    def apply(self):
        if self.running:return
        for iid in self.tree.selection():
            v=list(self.tree.item(iid,'values')); v[1:4]=[self.params[k].get() for k in ('Width (mm)','Thickness (mm)','Gauge length (mm)')]; self.tree.item(iid,values=v)
    def edit_dimensions(self,event):
        if self.running:return
        iid=self.tree.identify_row(event.y)
        if not iid:return
        vals=list(self.tree.item(iid,'values')); win=tk.Toplevel(self.root); win.title(vals[0]); variables=[]
        for i,title in enumerate(['Width (mm)','Thickness (mm)','Gauge length (mm)']):
            ttk.Label(win,text=title).grid(row=i,column=0,padx=10,pady=5)
            v=tk.StringVar(value=vals[i+1]); variables.append(v); ttk.Entry(win,textvariable=v).grid(row=i,column=1,padx=10)
        def save():
            try:
                dimensions=[float(v.get()) for v in variables]
                if min(dimensions)<=0:raise ValueError()
            except ValueError:messagebox.showerror('Invalid dimensions','Enter positive numbers');return
            vals[1:4]=dimensions;self.tree.item(iid,values=vals);win.destroy()
        ttk.Button(win,text='Save',command=save).grid(row=3,column=1,pady=10)
    def save_folder(self):
        p=filedialog.askdirectory()
        if p:self.save.set(p)
    def manual(self):
        if self.running:return
        selected=self.tree.selection()
        if len(selected)!=1:messagebox.showinfo('Select sample','Select one sample');return
        data=next(v for v in self.items.values() if v['iid']==selected[0]); win=tk.Toplevel(self.root);win.title('Manual fracture strain (%)');variables={}
        ttk.Label(win,text='Blank = automatic detection. Enter fracture strain in %.').grid(row=0,column=0,columnspan=2,padx=10,pady=8)
        for row,label in enumerate(data['labels'],1):
            ttk.Label(win,text=label).grid(row=row,column=0,padx=10)
            var=tk.StringVar(value=str(data['overrides'].get(label,'')));variables[label]=var;ttk.Entry(win,textvariable=var).grid(row=row,column=1,padx=10,pady=3)
        def save():
            try:
                values={k:float(v.get()) for k,v in variables.items() if v.get().strip()}
                if any(not (0<=v<float('inf')) for v in values.values()):raise ValueError()
            except ValueError:messagebox.showerror('Invalid strain','Enter finite nonnegative values');return
            data['overrides']=values;win.destroy()
        ttk.Button(win,text='Save',command=save).grid(row=len(variables)+1,column=1,pady=10)
    def start(self):
        if self.running:return
        try:
            configs=[]
            for p,data in self.items.items():
                dims=[float(self.params['Width (mm)'].get()),float(data['thickness'].get()),float(self.params['Gauge length (mm)'].get())]
                if any(not math.isfinite(v) or v<=0 for v in dims):raise ValueError('Dimensions must be finite and positive')
                configs.append((p,*dims,data['overrides'].copy()))
            if not configs:raise ValueError('Select at least one CSV')
            fit_min=float(self.params['Fit min (%)'].get());fit_max=float(self.params['Fit max (%)'].get());drop=float(self.params['Drop (%)'].get())/100
            if not 0<=fit_min<fit_max or not 0<drop<1:raise ValueError('Invalid fitting range or drop percentage')
            folder=Path(self.save.get())
            if not folder.is_dir():raise ValueError('Save folder must exist')
        except ValueError as e:messagebox.showerror('Check settings',str(e));return
        path=folder/f'Tensile_Analysis_{datetime.now():%Y%m%d_%H%M%S_%f}.xlsx'
        self.running=True;self.run_button.configure(state='disabled');self.status.set('Running...')
        smooth=self.smooth.get()
        def worker():
            try:
                samples=core.process_files(configs,path,fit_min,fit_max,drop,smooth,lambda s:self.events.put(('log',s)))
                self.events.put(('done',(path,samples)))
            except Exception as e:self.events.put(('error',str(e)))
        threading.Thread(target=worker,daemon=True).start()
    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='log':self.log.configure(state='normal');self.log.insert('end',value+'\n');self.log.see('end');self.log.configure(state='disabled')
                else:
                    self.running=False;self.run_button.configure(state='normal')
                    if kind=='error':self.status.set('Failed');messagebox.showerror('Analysis failed',value)
                    else:
                        path,samples=value;missing=sum(r['break_index'] is None for trials in samples.values() for _,r in trials)
                        self.status.set(f'Finished. Fracture not detected: {missing}')
                        messagebox.showinfo('Workbook saved',f'{path}\nFracture not detected: {missing}. Set manual points and rerun if needed.')
                        try:
                            if sys.platform=='win32':os.startfile(path)
                            elif sys.platform=='darwin':subprocess.run(['open',str(path)],check=True)
                        except Exception:pass
        except queue.Empty:pass
        self.root.after(100,self.poll)
    def close(self):
        if self.running:messagebox.showinfo('Analysis running','Wait for the current analysis to finish')
        else:self.root.destroy()

    def select_sample(self,p):
        if p not in self.items:return
        self.active=p;self.tree.selection_set(self.items[p]['iid']);self.schedule_preview()

    def schedule_preview(self,*args):
        if self.preview_job is not None:self.root.after_cancel(self.preview_job)
        self.preview_job=self.root.after(150,self.draw_preview)

    def draw_preview(self):
        self.preview_job=None;self.plot.delete('all')
        w=max(self.plot.winfo_width(),240);h=max(self.plot.winfo_height(),200)
        if self.active not in self.items:
            self.preview_title.set('Import CSV files or a folder');return
        data=self.items[self.active];index=data['choices'].index(data['trial'].get())
        label,raw=data['trials'][index]
        self.preview_title.set(f'{Path(self.active).stem} / Trial {index+1} / {label}')
        try:
            width=float(self.params['Width (mm)'].get());length=float(self.params['Gauge length (mm)'].get());thickness=float(data['thickness'].get())
            if any(not math.isfinite(v) or v<=0 for v in (width,length,thickness)):raise ValueError()
        except ValueError:
            self.plot.create_text(w/2,h/2,text='Enter this sample thickness (mm) to view the curve',font=('Arial',13))
            self.preview_note.set('Width and gauge length apply to all samples. Thickness is individual.');return
        x=raw[:,2]/length*100;y=raw[:,1]/(width*thickness);plot_y=y.copy()
        if self.smooth.get():
            try:
                result=core.analyze_trial(raw,width,thickness,length,float(self.params['Fit min (%)'].get()),float(self.params['Fit max (%)'].get()),float(self.params['Drop (%)'].get())/100,data['overrides'].get(label))
                plot_y,_=core.plot_values(result,True)
            except ValueError:pass
        xmax=max(float(x.max()),1e-12);ymax=max(float(y.max())*1.05,1e-12)
        left,right,top,bottom=85,w-30,25,h-60
        self.plot.create_rectangle(left,top,right,bottom,outline='black',width=1)
        for i in range(5):
            xx=left+(right-left)*i/4;yy=bottom-(bottom-top)*i/4
            self.plot.create_line(xx,bottom,xx,bottom-5);self.plot.create_line(left,yy,left+5,yy)
            self.plot.create_text(xx,bottom+16,text=f'{xmax*i/4:.3g}',font=('Arial',11))
            self.plot.create_text(left-8,yy,text=f'{ymax*i/4:.3g}',anchor='e',font=('Arial',11))
        self.plot.create_text((left+right)/2,h-16,text='Strain (%)',font=('Arial',12))
        self.plot.create_text(20,(top+bottom)/2,text='Stress (MPa)',angle=90,font=('Arial',12))
        points=[];bucket=max(1,len(x)//1200)
        for start in range(0,len(x),bucket):
            stop=min(len(x),start+bucket);part=plot_y[start:stop]
            for i in sorted(set([start,stop-1,start+int(np.argmin(part)),start+int(np.argmax(part))])):
                points.extend((left+x[i]/xmax*(right-left),bottom-max(0,plot_y[i])/ymax*(bottom-top)))
        if len(points)>=4:self.plot.create_line(*points,fill='#D62728',width=1.5)
        self.preview_note.set(f'{len(x)} points | Thickness: {thickness:g} mm | Includes post-fracture tail. Run generates Excel.')

if __name__=='__main__':
    root=tk.Tk();App(root);root.mainloop()
