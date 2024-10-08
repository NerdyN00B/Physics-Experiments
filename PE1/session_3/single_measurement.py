import numpy as np
import mydaq as md
# filesave dialog
import tkinter as tk
from tkinter import filedialog
import os

def find_nearest_idx(a, value):
    return (np.abs(a - value)).argmin()

samplerate = 200_000
duration = 1 # s
frequency = 1000 # Hz
amplitude = 3 # V

dir = os.getcwd()
dir += '/PE1/session_3'

root = tk.Tk()
root.withdraw()

savefile = filedialog.asksaveasfilename(filetypes=[('Numpy files', '.npy')],
                                         defaultextension='.npy',
                                         initialdir=dir,
                                         title='Save data as',
                                         confirmoverwrite=True,
                                         )

daq = md.MyDAQ(samplerate, 'myDAQ2')

time, waveform = daq.generateWaveform('sine',
                               samplerate=daq.samplerate,
                               frequency=frequency,
                               amplitude=amplitude,
                               duration=duration)

data = daq.readWrite(waveform)
data = data[:-samplerate//10]

np.save(savefile, data)

fourier = np.fft.fft(data)
freq = np.fft.fftfreq(len(data), 1/samplerate)

fourier_norm = np.abs(fourier)/len(data) * 2
fourier_norm = fourier_norm[:len(fourier)//2]

gain = 20 * np.log10(fourier_norm[find_nearest_idx(freq, frequency)]/amplitude)

print(f'Gain at {frequency} Hz: {gain:.2f} dB')