import numpy as np
import matplotlib.pyplot as plt
from mydaq import MyDAQ
from scipy.signal import argrelextrema

filename = "buis2_fourier.npy"

slice_end = 6000

fourier = np.abs(np.load(filename))[:slice_end]
angle = np.angle(np.load(filename))[:slice_end] % 2*np.pi
freq = np.fft.fftfreq(len(np.load(filename)), 1 / 44100)[:slice_end]

maxima = argrelextrema(fourier, np.greater, order=300)
print(maxima)

fig, ax = plt.subplots(2, dpi=300, layout='tight')

[ax[0].annotate(f"{freq[i]:.2f} Hz", (freq[i], fourier[i])) for i in maxima[0]]

ax[0].plot(freq, fourier)
ax[0].set_title("magnitudes")
ax[0].set_xlabel("Frequency $f$ [$Hz$]")
ax[0].set_ylabel("Amplitude $A$ [$a.u.$]")
ax[0].grid()

ax[1].scatter(freq, angle, marker='.')
ax[1].set_title("angles")
ax[1].set_xlabel("Frequency $f$ [$Hz$]")
ax[1].set_ylabel("Angle $\\theta$ [$rad$]")

fig.savefig(filename.strip('.npy') + '_analysed_angle.pdf')