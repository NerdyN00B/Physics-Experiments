import numpy as np
import matplotlib.pyplot as plt
from mydaq import MyDAQ

filename = "buis2.npy"
filename_compare = "buis2_phase_removed.npy"

duration = 1 # seconds
time = MyDAQ.getTimeArray(duration, 44100)
# time = time[:len(time) - 1]

slice_start = 0
slice_end = -1

time = time[slice_start:slice_end]

signal = np.load(filename)[slice_start:slice_end]
if filename_compare.endswith("fourier.npy"):
    signal_compare = np.fft.ifft(np.load(filename_compare))[slice_start:slice_end]
else:
    signal_compare = np.load(filename_compare)[slice_start:slice_end]

fig, ax = plt.subplots(layout='tight', dpi=300)

ax.plot(time, signal, label="Original")
ax.plot(time, signal_compare, label="Modified")
ax.set_xlabel("Time $T$ [$s$]")
ax.set_ylabel("Voltage $V$ [$V$]")
ax.legend()
ax.grid()
fig.savefig(filename_compare.strip('.npy') + '_compare(full).pdf')
