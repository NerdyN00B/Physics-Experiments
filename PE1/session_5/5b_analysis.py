import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from mydaq import MyDaq
import tkinter as tk
from tkinter import filedialog
import os

## Values of measurement
samplerate = 200_000
repeat = 5

## Prompt loading and load data
root = tk.Tk()
root.withdraw()

dir = os.getcwd() + '/PE1/session_5'

file_path = filedialog.askopenfilename(filetypes=[('Numpy files', '.npy')],
                                        initialdir=dir,
                                        title='Select data file',
                                        )

data = np.load(file_path)
frequencies = np.load(file_path.replace('.npy', '_frequencies.npy'))

data = data[:, :, :, :samplerate//10]

# Analyse data
full_transfer = MyDaq.get_transfer_functions(data,
                                           frequencies,
                                           repeat=repeat,
                                           samplerate=samplerate,
                                           integration_range=5,
                                           )

mean_gain, std_gain, mean_phase, std_phase = MyDaq.analyse_transfer(full_transfer)

fig, gain_ax, phase_ax, polar_ax = MyDaq.make_bode_plot(dpi=300,
                                                      layout='tight',
                                                      figsize=(16, 9))

## Plot and fit
# gain plot
MyDaq.plot_gain(gain_ax, frequencies, mean_gain, std_gain)

gain_ax.grid()

# phase plot
MyDaq.plot_phase(phase_ax, frequencies, mean_phase, std_phase)

phase_ax.grid()

# polar plot
MyDaq.plot_polar(polar_ax, mean_gain, mean_phase)

fig.savefig(file_path.replace('.npy', '.pdf'))