import numpy as np
import PE1.mydaq as md
import matplotlib.pyplot as plt

def find_nearest_idx(a, value):
    return (np.abs(a - value)).argmin()

samplerate = 200_000
duration = 1 # s
amplitude = 3 # V
frequency = 1000 # Hz

cap = 1.5e-9 # F
res = 1e5 # Ohm

daq = md.MyDAQ(samplerate, 'myDAQ2')

time, waveform = daq.generateWaveform('sine',
                                samplerate=daq.samplerate,
                                frequency=frequency,
                                amplitude=amplitude,
                                duration=duration
                                )

read = (daq.readWrite(waveform, read_channel=["ai0", "ai1"]))

data_in = read[0]
data_out = read[1]

# # For testing without mydaq
# time = np.linspace(0, duration, int(samplerate*duration))
# data_in = amplitude * np.sin(2 * np.pi * frequency * time)
# a_out = 10**(-3/20) * amplitude
# data_out = a_out * np.sin(2 * np.pi * frequency * time + np.pi/4)

data_in = np.asarray(data_in)[:-int(samplerate*0.1)] # remove last 0.1 seconds
data_out = np.asarray(data_out)[:len(data_in)] # ensure same length

fourier_in = np.fft.fft(data_in)
fourier_out = np.fft.fft(data_out)

frequencies = np.fft.fftfreq(len(data_in), 1/samplerate)
idx = find_nearest_idx(frequencies, frequency)

integration_range = 5

integrated_in = np.trapz(fourier_in[idx-integration_range:idx+integration_range],
                         frequencies[idx-integration_range:idx+integration_range])

integrated_out = np.trapz(fourier_out[idx-integration_range:idx+integration_range],
                          frequencies[idx-integration_range:idx+integration_range])

transfer = integrated_out / integrated_in


gain = 20 * np.log10(np.abs(transfer))
print(f'Gain at {frequency} Hz: {gain} dB')

angle = np.angle(transfer, deg=True)
print(f'Phase at {frequency} Hz: {angle} degrees')

fig, ax = plt.subplots()

time = time[:len(data_in)] # ensure same length as data

ax.plot(time, data_in, label='Input')
ax.plot(time, data_out, label='Output')

ax.set_title(f'Input and output signals with inset of first 1/{frequency} seconds')
ax.set_xlabel('Time [s]')
ax.set_ylabel('Amplitude [V]')
ax.legend()

axins = ax.inset_axes(
    [0.3, 0.3, 0.4, 0.4],
    xlim=(0, 1/frequency),
    xticklabels=[], yticklabels=[],
    )

axins.plot(time, data_in)
axins.plot(time, data_out)

ax.indicate_inset_zoom(axins, edgecolor='black')

plt.savefig('PE1/Session_4/figures/test.pdf')