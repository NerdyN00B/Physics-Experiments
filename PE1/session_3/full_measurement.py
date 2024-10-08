import numpy as np
import mydaq as md
# filesave dialog
import tkinter as tk
from tkinter import filedialog
import os
import analysis as an

samplerate = 200_000
duration = 1 # s
ammount = 100 # number of measured frequencies in logspace from 10 to 10000 Hz
amplitude = 3 # V

cap = 1.5e-9 # F
res = 1e5 # Ohm

frequencies = np.logspace(1, 4, ammount) # Hz

dir = os.getcwd()
dir += '/PE1/session_3'

root = tk.Tk()
root.withdraw()

savefile = filedialog.asksaveasfilename(filetypes=[('Numpy files', '.npy')],
                                         defaultextension='.npy',
                                         initialdir=dir,
                                         title='Save raw data as',
                                         confirmoverwrite=True,
                                         )

daq = md.MyDAQ(samplerate, 'myDAQ2')

data = []
for frequency in frequencies:
    time, waveform = daq.generateWaveform('sine',
                                samplerate=daq.samplerate,
                                frequency=frequency,
                                amplitude=amplitude,
                                duration=duration)

    data.append(daq.readWrite(waveform))

np.save(savefile, np.asarray(data))
np.save(savefile.replace('.npy', '_frequencies.npy'), frequencies)

data = np.asarray(data)

data = data[:,:-samplerate//10] # remove last 100 ms of data because of readwrite desync

spectrum = an.get_spectrum(data, frequencies)
np.save(savefile.replace('.npy', '_spectrum.npy'), spectrum)

fig, ax = an.plot_spectrum(spectrum, frequencies, cap, res)
popt, pcov = an.fit(ax, frequencies, spectrum, cap, res)
ax.legend()
fig.savefig(savefile.replace('.npy', '_spectrum.pdf'))
fig.show()

error = np.sqrt(np.diag(pcov))
print(f'Capacitance: {popt[0]:.2e} F +/- {error[0]:.2e} F')
print(f'Resistance: {popt[1]:.2e} Ohm +/- {error[1]:.2e} Ohm')
