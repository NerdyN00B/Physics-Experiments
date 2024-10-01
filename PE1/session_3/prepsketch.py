import numpy as np
import matplotlib.pyplot as plt



cap = 1.5e-9
res = 1e6

f = np.logspace(0, 5, 1000)

def output_fraction(f, cap, res):
    x_c= 1 / (2 * np.pi * f * cap)
    return res / np.sqrt(res**2 + x_c**2)

def cutoff(res, cap):
    return 1 / (2 * np.pi * res * cap)

fig, ax = plt.subplots(dpi=300, layout='tight')

ydata = 20*np.log10(output_fraction(f, cap, res))

ax.semilogx(f, ydata, c='k', label='transfer function')
ax.vlines(cutoff(res, cap), np.min(ydata), 0, colors='r', linestyles='dashed',
          label='Cutoff frequency')
ax.hlines(-3, 0, np.max(f), colors='r', linestyles='dashed')
ax.annotate(f'Cutoff frequency {cutoff(res, cap):.2f} Hz',
            xy=(cutoff(res, cap), -3),
            xytext=(-100, 20),
            textcoords='offset points',
            arrowprops=dict(facecolor='black', arrowstyle='->'))
ax.set_yticks(np.append(ax.get_yticks(), -3))
ax.set_xlabel('Frequency [Hz]')
ax.set_ylabel('Gain [dB]')
ax.grid()
ax.set_title('transfer function for high-pass filter')
fig.savefig('PE1/session_3/highpass.pdf')
plt.show()
