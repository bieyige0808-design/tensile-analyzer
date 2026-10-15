"""Small controls shared by sample and trial settings."""
from decimal import Decimal, InvalidOperation
import tkinter as tk
from tkinter import ttk

def shift_control(parent,variable):
    frame=ttk.Frame(parent)
    def step(direction):
        try:value=Decimal(variable.get() or '0')
        except InvalidOperation:value=Decimal('0')
        if not value.is_finite():value=Decimal('0')
        variable.set(format(value+Decimal('0.01')*direction,'.2f'))
    tk.Button(frame,text='−',width=2,command=lambda:step(-1),repeatdelay=350,repeatinterval=65).pack(side='left')
    ttk.Entry(frame,textvariable=variable,width=7).pack(side='left',padx=2)
    tk.Button(frame,text='+',width=2,command=lambda:step(1),repeatdelay=350,repeatinterval=65).pack(side='left')
    return frame
