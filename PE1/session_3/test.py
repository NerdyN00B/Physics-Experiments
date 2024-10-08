import numpy as np
import mydaq as md
import matplotlib.pyplot as plt

# samplerate = 200_000
# duration = .9 # s
# frequency = 1000 # Hz
# amplitude = 3 # V

# time, waveform = md.MyDAQ.generateWaveform('sine',
#                                samplerate=200000,
#                                frequency=frequency,
#                                amplitude=amplitude,
#                                duration=duration)

i = 50
samplerate = 200_000

data = np.load(r'C:\\Users\\masla\\Documents\\School\\Natuurkunde WO\\Jaar 2\\Physics-Experiments\\PE1\\session_3\\1000_frequencies.npy')
fouqs = np.load(r'C:\\Users\\masla\\Documents\\School\\Natuurkunde WO\\Jaar 2\\Physics-Experiments\\PE1\\session_3\\1000_frequencies_frequencies.npy')

data_i = data[i, :-samplerate//10]

fourier_i = np.fft.fft(data_i)
freqs = np.fft.fftfreq(len(data_i), 1/samplerate)

fig, ax = plt.subplots()
plt.semilogx(freqs[:len(freqs)//2], abs(fourier_i[:len(fourier_i)//2]), marker='.')
plt.show()


# fig, ax = plt.subplots()

# ax.plot(time, waveform)
# ax.plot(time, data)

# ax.set_xlabel('time [$s$]')
# ax.set_ylabel('Voltage [$V$]')

# plt.show()

# fig.savefig('1000Hz.pdf')