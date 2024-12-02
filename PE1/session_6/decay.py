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
frequency = 0.8
duration = 60
order = 100


# Prompt save file
dir = os.getcwd()
dir += '/PE1/session_6'

root = tk.Tk()
root.withdraw()

savefile = filedialog.asksaveasfilename(filetypes=[('Numpy files', '.npy')],
                                         defaultextension='.npy',
                                         initialdir=dir,
                                         title='Save raw data as',
                                         confirmoverwrite=True,
                                         )


# Start of the measurement code
daq = MyDAQ(200_000, 'myDAQ2')

signal = daq.generateWaveform('sine', daq.samplerate, frequency, 10)

daq.write(signal)
data = daq.read(duration=duration)

# Save data
np.save(savefile, data)

# Analyse data
time = daq.getTimeArray(10, daq.samplerate)

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

fig.savefig(savefile.replace('.npy', '.pdf'))