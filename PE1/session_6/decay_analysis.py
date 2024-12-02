import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.signal import argrelmax
from mydaq import MyDAQ
import tkinter as tk
from tkinter import filedialog
import os


def exponential_decay(t, C, tau, offset):
    return C * np.exp(-t / tau) + offset

# Important varialbles
samplerate = 200_000
frequency = 0.8
duration = 60
order = 100


# Prompt save file
dir = os.getcwd()
dir += '/PE1/session_6'

root = tk.Tk()
root.withdraw()

## Prompt loading and load data
root = tk.Tk()
root.withdraw()

dir = os.getcwd() + '/PE1/session_5'

file_path = filedialog.askopenfilename(filetypes=[('Numpy files', '.npy')],
                                        initialdir=dir,
                                        title='Select data file',
                                        )

data = np.load(file_path)


# Analyse data
time = MyDAQ.getTimeArray(10, samplerate)

fig, ax = plt.subplots(dpi=300, figsize=(16, 9))

ax.scatter(time, data, '.k', label='full measurement')

maxima = argrelmax(data, order=order)[0]
maxima_time = time[maxima]
maxima_data = data[maxima]

ax.scatter(maxima_time, maxima_data, 'or', label='maxima')

popt, pcov = curve_fit(exponential_decay,
                       maxima_time, maxima_data,
                       p0=[10, 0.1, 0])

fit_error = np.sqrt(np.diag(pcov))
fit_label = f'Fit: C = {popt[0]:.2f} $\pm$ {fit_error[0]:.2f}, '
fit_label += f'$\\tau$ = {popt[1]:.2f} $\pm$ {fit_error[1]:.2f}, '
fit_label += f'offset = {popt[2]:.2f} $\pm$ {fit_error[2]:.2f}'

ax.plot(time, exponential_decay(time, *popt), 'r--', label=fit_label)

ax.set_xlabel('Time [s]')
ax.set_ylabel('Voltage [V]')

ax.grid()
ax.legend()

fig.savefig(file_path.replace('.npy', '.pdf'))