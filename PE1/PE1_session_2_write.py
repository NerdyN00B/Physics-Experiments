import numpy as np
import matplotlib.pyplot as plt
from mydaq import MyDAQ

daq = MyDAQ(44100)

filename = input("Enter the name of the file to read the data from: ")

if filename.endswith("fourier.npy"):
    signal = np.fft.ifft(np.load(filename))
else:
    signal = np.load(filename)

signal /= 1 # Lower the signal to safe audio levels

daq.write(signal)