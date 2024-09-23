import numpy as np
import matplotlib.pyplot as plt
from mydaq import MyDAQ

filename = "filename.npy"
filename_compare = "filename_compare.npy"

duration = 1 # seconds
time = MyDAQ.getTimeArray(duration, 44100)

slice_start = 0
slice_end = -1

signal = np.load(filename)[slice_start:slice_end]
signal_compare = np.load(filename_compare)[slice_start:slice_end]

fig, ax = plt.subplots(layout='tight', dpi=300)

ax.plot(time, signal, label="Original")
ax.plot(time, signal_compare, label="Modified")
ax.set_xlabel("Time $T$ [$s$]")
ax.set_ylabel("Voltage $V$ [$V$]")
ax.legend()
ax.grid()
plt.show()
