"""Per-trial settings, results, curves and source data."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import numpy as np
import tensile_core as core

class TrialDetails:
    def __init__(self,app,path):
        self.app=app;self.path=path;self.data=app.items[path];self.raw_index=None
        self.window=tk.Toplevel(app.root);self.window.title(f'Experiments — {Path(path).stem}')
        self.window.geometry('1220x820');self.window.minsize(950,680)
        outer=ttk.Frame(self.window,padding=10);outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='Blank trial settings inherit the sample values. Edits and inclusion choices are retained when this window closes.').pack(anchor='w')
        table_box=ttk.Frame(outer);table_box.pack(fill='x',pady=6)
        self.canvas=tk.Canvas(table_box,height=180,highlightthickness=0)
        scroll=ttk.Scrollbar(table_box,orient='vertical',command=self.canvas.yview)
        scroll.pack(side='right',fill='y');self.canvas.pack(fill='x',expand=True)
        self.canvas.configure(yscrollcommand=scroll.set)
        self.rows=ttk.Frame(self.canvas);item=self.canvas.create_window((0,0),window=self.rows,anchor='nw')
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(item,width=e.width))
        self.rows.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        titles=['Include in mean','Trial','Thickness\n(mm)','Fit min\n(%)','Fit max\n(%)','Strength\n(MPa)','Modulus\n(GPa)','Break strain\n(%)','Toughness\n(MJ/m3)','Status']
        for col,title in enumerate(titles):ttk.Label(self.rows,text=title).grid(row=0,column=col,padx=5,sticky='w')
        self.result_vars=[]
        for index,(label,raw) in enumerate(self.data['trials'],1):
            options=self.data['options'][label]
            ttk.Checkbutton(self.rows,variable=options['included']).grid(row=index,column=0)
            ttk.Label(self.rows,text=f'{index}: {label}').grid(row=index,column=1,padx=5)
            for col,key in enumerate(('thickness','fit_lo','fit_hi'),2):
                ttk.Entry(self.rows,textvariable=options[key],width=9).grid(row=index,column=col,padx=4,pady=4)
            values=[tk.StringVar(value='—') for _ in range(5)];self.result_vars.append(values)
            for col,var in enumerate(values,5):ttk.Label(self.rows,textvariable=var,wraplength=180).grid(row=index,column=col,padx=5,sticky='w')
        self.note=tk.StringVar();ttk.Label(outer,textvariable=self.note).pack(anchor='w')
        self.plot=tk.Canvas(outer,bg='white',height=300,highlightthickness=0)
        self.plot.pack(fill='both',expand=True,pady=6);self.plot.bind('<Configure>',lambda e:self.refresh())
        raw_controls=ttk.Frame(outer);raw_controls.pack(fill='x')
        ttk.Label(raw_controls,text='Source data for trial:').pack(side='left')
        self.raw_choice=tk.StringVar(value=self.data['choices'][0])
        combo=ttk.Combobox(raw_controls,textvariable=self.raw_choice,values=self.data['choices'],state='readonly',width=25)
        combo.pack(side='left',padx=10);combo.bind('<<ComboboxSelected>>',lambda e:self.show_raw())
        raw_frame=ttk.Frame(outer);raw_frame.pack(fill='x',pady=6)
        self.raw_table=ttk.Treeview(raw_frame,columns=('time','force','stroke'),show='headings',height=5)
        for col,title in [('time','Time (s)'),('force','Force (N)'),('stroke','Stroke (mm)')]:self.raw_table.heading(col,text=title)
        sb=ttk.Scrollbar(raw_frame,orient='vertical',command=self.raw_table.yview)
        self.raw_table.configure(yscrollcommand=sb.set);sb.pack(side='right',fill='y');self.raw_table.pack(fill='x')
        self.window.after(50,self.refresh);self.show_raw()

    def show_raw(self):
        index=self.data['choices'].index(self.raw_choice.get())
        if index==self.raw_index:return
        self.raw_index=index;self.raw_table.delete(*self.raw_table.get_children())
        for row in self.data['trials'][index][1]:self.raw_table.insert('','end',values=[f'{v:.7g}' for v in row])

    def refresh(self):
        if not self.window.winfo_exists():return
        try:options=self.app.evaluate_sample(self.data)
        except ValueError as e:
            self.note.set(f'Check sample dimensions / trial settings: {e}')
            self.plot.delete('all')
            for row in self.result_vars:
                for var in row:var.set('—')
            return
        curves=[];eligible=0
        length=float(self.app.params['Gauge length (mm)'].get());width=float(self.app.params['Width (mm)'].get())
        for i,((label,raw),result,variables) in enumerate(zip(self.data['trials'],self.data['results'],self.result_vars)):
            included=options[label]['included'];eligible+=int(included)
            if result is None:
                for var in variables[:4]:var.set('—')
                variables[4].set(self.data['errors'][i])
            else:
                for var,key in zip(variables,('strength','modulus','break_strain','toughness')):
                    value=result[key];var.set(f'{value:.5g}' if value is not None else '—')
                variables[4].set(result['break_status']+(' / excluded' if not included else ''))
            x=raw[:,2]/length*100;y=raw[:,1]/(width*options[label]['thickness'])
            if result is not None and self.app.smooth.get():y,_=core.plot_values(result,True)
            curves.append((label,x,y,options[label],included))
        self.note.set(f'{eligible}/{len(curves)} trials selected for averaging. Excluded trials remain visible as dashed curves and remain in Excel.')
        self.draw(curves)

    def draw(self,curves):
        c=self.plot;c.delete('all');w=max(c.winfo_width(),350);h=max(c.winfo_height(),200)
        left,right,top,bottom=80,max(170,w-200),25,h-50
        xmax=max(max(float(x.max()) for _,x,_,_,_ in curves),1e-12)
        ymax=max(max(float(y.max()) for _,_,y,_,_ in curves)*1.05,1e-12)
        c.create_rectangle(left,top,right,bottom)
        for i in range(5):
            xx=left+(right-left)*i/4;yy=bottom-(bottom-top)*i/4
            c.create_text(xx,bottom+14,text=f'{xmax*i/4:.3g}',font=('Arial',10))
            c.create_text(left-8,yy,text=f'{ymax*i/4:.3g}',anchor='e',font=('Arial',10))
        c.create_text((left+right)/2,h-12,text='Strain (%)');c.create_text(17,(top+bottom)/2,text='Stress (MPa)',angle=90)
        colors=['#D62728','#1F77B4','#2CA02C','#9467BD','#FF7F0E','#17BECF','#8C564B']
        for index,(label,x,y,settings,included) in enumerate(curves):
            color=colors[index%len(colors)];points=[];bucket=max(1,len(x)//800)
            for start in range(0,len(x),bucket):
                stop=min(len(x),start+bucket);part=y[start:stop]
                for i in sorted(set([start,stop-1,start+int(np.argmin(part)),start+int(np.argmax(part))])):
                    points.extend((left+x[i]/xmax*(right-left),bottom-max(0,y[i])/ymax*(bottom-top)))
            if len(points)>=4:c.create_line(*points,fill=color,width=1.5,dash=() if included else (4,4))
            bold=[]
            for i in np.flatnonzero((x>=settings['fit_min'])&(x<=settings['fit_max'])):
                bold.extend((left+x[i]/xmax*(right-left),bottom-max(0,y[i])/ymax*(bottom-top)))
            if len(bold)>=4:c.create_line(*bold,fill=color,width=4)
            c.create_text(right+15,top+15+index*22,text=f'{index+1}: {label}'+(' (excluded)' if not included else ''),fill=color,anchor='w')
