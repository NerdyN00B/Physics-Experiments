import numpy as np
import PE1.mydaq as md
# filesave dialog
import tkinter as tk
from tkinter import filedialog
import os

samplerate = 200_000
duration = 1 # s
ammount = 15 # number of measured frequencies in logspace from 10 to 10000 Hz
amplitude = 3 # V
extra_points = 10 # number of extra points arround the frequency of interest
repeat = 4 # number of times to repeat the measurement

foi = 1061 # Hz - frequency of interest

frequencies = np.logspace(1, 4, ammount) # Hz

if extra_points > 0:
    extra_freq = np.linspace(foi - extra_points//2, foi + extra_points//2, extra_points)
    frequencies = np.concatenate((frequencies, extra_freq))
    frequencies = np.sort(frequencies)

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

for i in range(repeat):
    data_in = []
    data_out = []
    for frequency in frequencies:
        waveform = daq.generateWaveform('sine',
                                            samplerate=daq.samplerate,
                                            frequency=frequency,
                                            amplitude=amplitude,
                                            duration=duration
                                            )[1]

        read = (daq.readWrite(waveform, read_channel=["ai0", "ai1"]))
        data_in.append(read[0])
        data_out.append(read[1])
        
    data_in = np.asarray(data_in)
    data_out = np.asarray(data_out)
    data = np.stack((data_in, data_out))
    if i > 0:
        np.save(savefile.replace('.npy', f'_{i}.npy'), data)
    else:
        np.save(savefile, data)

np.save(savefile.replace('.npy', '_frequencies.npy'), frequencies)