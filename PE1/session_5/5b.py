import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from mydaq import MyDaq
import tkinter as tk
from tkinter import filedialog
import os

## Prompt save file
dir = os.getcwd()
dir += '/PE1/session_5'

root = tk.Tk()
root.withdraw()

savefile = filedialog.asksaveasfilename(filetypes=[('Numpy files', '.npy')],
                                         defaultextension='.npy',
                                         initialdir=dir,
                                         title='Save raw data as',
                                         confirmoverwrite=True,
                                         )

## Start of the measurement code

repeat = 5

daq = MyDaq(200_000, 'myDAQ2')

frequencies = np.logspace(1, 4, 25)

data = daq.measure_spectrum(frequencies,
                            duration=1,
                            amplitude=3,
                            repeat=repeat,
                            )

# Save data
np.save(savefile, data)
np.save(savefile.replace('.npy', '_frequencies.npy'), frequencies)

# Analyse data
full_transfer = daq.get_transfer_functions(data,
                                           frequencies,
                                           repeat=repeat,
                                           samplerate=daq.samplerate,
                                           integration_range=5,
                                           )

mean_gain, std_gain, mean_phase, std_phase = daq.analyse_transfer(full_transfer)

fig, gain_ax, phase_ax, polar_ax = daq.make_bode_plot(dpi=300,
                                                      layout='tight',
                                                      figsize=(16, 9))

## Plot
# gain plot
daq.plot_gain(gain_ax, frequencies, mean_gain, std_gain)

gain_ax.grid()

# phase plot
daq.plot_phase(phase_ax, frequencies, mean_phase, std_phase)

phase_ax.grid()

# polar plot
daq.plot_polar(polar_ax, mean_gain, mean_phase)

fig.savefig(savefile.replace('.npy', '.pdf'))
