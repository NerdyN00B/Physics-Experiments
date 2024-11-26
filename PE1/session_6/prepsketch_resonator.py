import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


omega_0 = 1*np.pi*2
q_factor = 10

f = np.logspace(-0.5, 1, 10000)
omega = f * 2 * np.pi

def transfer_function(omega, omega_0, q_factor):
    return 1 / (1 - omega**2 / omega_0**2 + 1j * omega / omega_0 / q_factor)


fig = plt.figure(dpi=300, layout='tight', figsize=(16, 9))

gs = gridspec.GridSpec(4, 2, figure=fig)
ax = fig.add_subplot(gs[:2, 0])

output_signal = transfer_function(omega, omega_0, q_factor)

magnitude = 20*np.log10(np.abs(output_signal))

ax.semilogx(f, magnitude, c='k', label='transfer function')

ax.vlines(omega_0/2/np.pi, np.min(magnitude), np.max(magnitude),
          colors='r', linestyles='dashed',
          label='Resonance frequency')
# ax.hlines(np.max(magnitude), 0, np.max(f), colors='r', linestyles='dashed')
ax.annotate(f'Resonant frequency {omega_0/2/np.pi:.0f} $Hz$',
            xy=(omega_0/2/np.pi, np.max(magnitude)),
            xytext=(50, -20),
            textcoords='offset points',
            arrowprops=dict(facecolor='black', arrowstyle='->'))

# ax.set_yticks(np.append(ax.get_yticks(), -3))
ax.set_xlabel('Frequency $f$ [$Hz$]')
ax.set_ylabel('Gain [$dB$]')
ax.set_title('magnitude transfer function for high-pass filter')

# axins = ax.inset_axes(
#     [0.1, 0.1, 0.3, 0.5],
#     transform=ax.transAxes,
#     xlim=(omega_0-1400, omega_0+1400),
#     ylim=(-3, max(magnitude)+3),)
# 
# axins.semilogx(f, magnitude, c='k')
# axins.vlines(omega_0, np.min(magnitude), np.max(magnitude),
#              colors='r', linestyles='dashed')

# ax.indicate_inset_zoom(axins)


ax.text(-0.01, 1.1, '(a)', transform=ax.transAxes, 
        fontsize=16, 
        fontweight='bold', 
        va='top', 
        ha='right')

ax.grid(True, 'both')

ax2 = fig.add_subplot(gs[2:, 0])

angle = np.angle(output_signal)
angle = np.rad2deg(angle)

ax2.semilogx(f, angle, c='k', label='transfer function')

ax2.set_xlabel('Frequency $f$ [$Hz$]')
ax2.set_ylabel('Phase [$°$]')
ax2.set_title('phase transfer function for high-pass filter')
ax2.grid(True, 'both')

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

fig.savefig('PE1/session_6/figures/resonator.pdf')
fig.savefig('PE1/session_6/figures/resonator.png')
