import numpy as np
import tkinter as tk
from tkinter import filedialog
import os


dir = os.getcwd()
dir += '/PE1/session_3'

root = tk.Tk()
root.withdraw()

file_path = filedialog.asksaveasfilename(filetypes=[('Numpy files', '.npy')],
                                         defaultextension='.npy',
                                         initialdir=dir,
                                         title='Save file as',
                                         confirmoverwrite=True,
                                         )