import numpy as np
import tkinter as tk
from tkinter import filedialog
import os


dir = os.getcwd()

dir += '/PE1/session_3'

root = tk.Tk()
root.withdraw()

file_path = filedialog.asksaveasfilename(filetypes=[('Numpy files', '.npy'),
                                                     ('Text files', '.txt')],
                                         defaultextension='.npy',
                                         initialdir=dir,
                                         title='Save file as...',
                                         confirmoverwrite=True,
                                         )

print(file_path)

if file_path.endswith('.npy'):
    np.save(file_path, np.random.rand(10, 10))
elif file_path.endswith('.txt'):
    np.savetxt(file_path, np.random.rand(10, 10))