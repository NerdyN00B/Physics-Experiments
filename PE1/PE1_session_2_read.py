import numpy as np
import matplotlib.pyplot as plt
from mydaq import MyDAQ

daq = MyDAQ(44100)
duration = 1 # seconds

signal = daq.read(duration)
time = MyDAQ.getTimeArray(duration, daq.samplerate)

filename = input("Enter the name of the file to save the data to: ")

np.save(filename, signal)

fourier = np.fft.fft(signal)
np.save(filename + "_fourier", fourier)

fig, ax = plt.subplots(2, 1, layout='tight')
ax[0].plot(time, signal)
ax[0].set_title("Time domain")
ax[0].set_xlabel("Time $T$ [$s$]")
ax[0].set_ylabel("Voltage $V$ [$V$]")

freq = np.fft.fftfreq(len(fourier), 1 / daq.samplerate)
ax[1].semilogy(freq//2, np.abs(fourier)//2)
ax[1].set_title("Frequency domain")
ax[1].set_xlabel("Frequency $f$ [$Hz$]")
ax[1].set_ylabel("Amplitude $A$ [$a.u.$]")