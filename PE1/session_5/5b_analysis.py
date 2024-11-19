import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from mydaq import MyDAQ as MyDaq
import tkinter as tk
from tkinter import filedialog
import os

## Values of measurement
samplerate = 200_000
repeat = 3

def pass_filter(omega, omega_0, n):
    return 1 / (1 + (omega / omega_0)**n)

def gain_transfer(omega, omega_0, n):
    return 20 * np.log10(abs(pass_filter(omega, omega_0, n)))
def phase_transfer(omega, omega_0, n):
    return np.angle(pass_filter(omega, omega_0, n))


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

# Analyse data
full_transfer = MyDaq.get_transfer_functions(data,
                                           frequencies,
                                           repeat=repeat,
                                           samplerate=samplerate,
                                           integration_range=1,
                                           )


mean_gain, std_gain, mean_phase, std_phase = MyDaq.analyse_transfer(full_transfer)


fig, gain_ax, phase_ax, polar_ax = MyDaq.make_bode_plot(dpi=300,
                                                      layout='tight',
                                                      figsize=(16, 9))

## Plot and fit
# gain plot
MyDaq.plot_gain(gain_ax, frequencies, mean_gain, std_gain)
popt_gain, pcov_gain = curve_fit(gain_transfer,
                                 frequencies*2*np.pi,
                                 mean_gain,
                                 p0=[12000, 2],
                                 sigma=std_gain,
                                 )

print(popt_gain)
gain_ax.plot(frequencies,
             gain_transfer(frequencies*2*np.pi, *popt_gain),
             'r--')


gain_ax.grid()

# phase plot
MyDaq.plot_phase(phase_ax, frequencies, mean_phase, std_phase)

phase_ax.grid()

# polar plot
MyDaq.plot_polar(polar_ax, mean_gain, mean_phase)

fig.savefig(file_path.replace('.npy', '_analysed.pdf'))