import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec



cap = 1.5e-9
res = 1e5

f = np.logspace(0, 5, 1000)
omega = f * 2 * np.pi

def transfer_function(omega, res, cap):
    iwrc = 1j * omega * res * cap
    return iwrc / (1 + iwrc)


def cutoff(res, cap):
    return 1 / (2 * np.pi * res * cap)


fig = plt.figure(dpi=300, layout='tight', figsize=(16, 9))

gs = gridspec.GridSpec(4, 2, figure=fig)
ax = fig.add_subplot(gs[:2, 0])


output_signal = transfer_function(omega, cap, res)

magnitude = 20*np.log10(np.abs(output_signal))

ax.semilogx(f, magnitude, c='k', label='transfer function')
ax.vlines(cutoff(res, cap), np.min(magnitude), 0, colors='r', linestyles='dashed',
          label='Cutoff frequency')
ax.hlines(-3, 0, np.max(f), colors='r', linestyles='dashed')
ax.annotate(f'Cutoff frequency {cutoff(res, cap):.0f} $Hz$',
            xy=(cutoff(res, cap), -3),
            xytext=(-100, 20),
            textcoords='offset points',
            arrowprops=dict(facecolor='black', arrowstyle='->'))

ax.set_yticks(np.append(ax.get_yticks(), -3))
ax.set_xlabel('Frequency $f$ [$Hz$]')
ax.set_ylabel('Gain [$dB$]')
ax.set_title('magnitude transfer function for high-pass filter')

ax.text(-0.01, 1.1, '(a)', transform=ax.transAxes, 
        fontsize=16, 
        fontweight='bold', 
        va='top', 
        ha='right')

ax.grid()

ax2 = fig.add_subplot(gs[2:, 0])

angle = np.angle(output_signal)
angle = np.rad2deg(angle)

ax2.semilogx(f, angle, c='k', label='transfer function')
ax2.vlines(cutoff(res, cap), np.min(angle), 90, 
           colors='r', 
           linestyles='dashed',
           label='Cutoff frequency')
ax2.hlines(45, 0, np.max(f), colors='r', linestyles='dashed')
ax2.annotate(f'Cutoff frequency {cutoff(res, cap):.0f} $Hz$',
            xy=(cutoff(res, cap), 45),
            xytext=(25, 20),
            textcoords='offset points',
            arrowprops=dict(facecolor='black', arrowstyle='->'))

ax2.set_yticks(np.append(ax2.get_yticks(), [90, 45]))
ax2.set_xlabel('Frequency $f$ [$Hz$]')
ax2.set_ylabel('Phase [$°$]')
ax2.set_title('phase transfer function for high-pass filter')
ax2.grid()

ax2.text(-0.01, 1.1, '(b)', transform=ax2.transAxes, 
         fontsize=16, 
         fontweight='bold', 
         va='top', 
         ha='right')

ax3 = fig.add_subplot(gs[:, 1], projection='polar')

ax3.plot(np.angle(output_signal), np.abs(output_signal), 
         c='k', 
         label='transfer function')

ax3.set_title('Polar plot of transfer function')

ax3.text(0.1, 1, '(c)', transform=ax3.transAxes,
         fontsize=16, 
         fontweight='bold', 
         va='top', 
         ha='right')

fig.savefig('PE1/session_4/highpass.pdf')
