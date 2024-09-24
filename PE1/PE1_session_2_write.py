import numpy as np
import matplotlib.pyplot as plt
from mydaq import MyDAQ

daq = MyDAQ(44100)

filename = "buis2_magnitude_removed.npy"

if filename.endswith("fourier.npy"):
    signal = np.fft.ifft(np.load(filename))
else:
    signal = np.load(filename)

signal *= .4 # Lower the signal to safe audio levels

daq.write(signal)