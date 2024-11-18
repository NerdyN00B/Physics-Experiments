import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec



cap = 50e-9
res = 500
ind = 100e-3

f = np.logspace(1.5, 5, 10000)
omega = f * 2 * np.pi

def transfer_function(omega, res, cap, ind):
    iwc = 1j * omega * cap
    iwl = 1j * omega * ind
    return (1/iwc) / (res + (1/iwc) + iwl)
    # return 1 / (1j * omega * res * cap + 1 - (omega**2 * cap * ind))


# def cutoff(res, cap):
#     return 1 / (2 * np.pi * res * cap)

def natural(cap, ind):
    return 1 / np.sqrt(cap * ind) / (2 * np.pi)

def q_factor(res, cap, ind):
    return 1/res * np.sqrt(ind/cap)

print(f'Natural frequency: {natural(cap, ind)}')
print(f'Q factor: {q_factor(res, cap, ind)}')

fig = plt.figure(dpi=300, layout='tight', figsize=(16, 9))

gs = gridspec.GridSpec(4, 2, figure=fig)
ax = fig.add_subplot(gs[:2, 0])

output_signal = transfer_function(omega, res, cap, ind)

magnitude = 20*np.log10(np.abs(output_signal))

ax.semilogx(f, magnitude, c='k', label='transfer function')

ax.vlines(natural(cap=cap, ind=ind), np.min(magnitude), np.max(magnitude),
          colors='r', linestyles='dashed',
          label='Resonance frequency')
# ax.hlines(np.max(magnitude), 0, np.max(f), colors='r', linestyles='dashed')
ax.annotate(f'Resonant frequency {natural(cap=cap, ind=ind):.0f} $Hz$',
            xy=(natural(cap=cap, ind=ind), np.max(magnitude)),
            xytext=(50, -20),
            textcoords='offset points',
            arrowprops=dict(facecolor='black', arrowstyle='->'))

# ax.set_yticks(np.append(ax.get_yticks(), -3))
ax.set_xlabel('Frequency $f$ [$Hz$]')
ax.set_ylabel('Gain [$dB$]')
ax.set_title('magnitude transfer function for high-pass filter')

axins = ax.inset_axes(
    [0.1, 0.1, 0.3, 0.5],
    transform=ax.transAxes,
    xlim=(natural(cap=cap, ind=ind)-1400, natural(cap=cap, ind=ind)+1400),
    ylim=(-3, max(magnitude)+3),)

axins.semilogx(f, magnitude, c='k')
axins.vlines(natural(cap=cap,ind=ind), np.min(magnitude), np.max(magnitude),
             colors='r', linestyles='dashed')

ax.indicate_inset_zoom(axins)


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
# ax2.vlines(cutoff(res, cap), np.min(angle), 90, 
#            colors='r', 
#            linestyles='dashed',
#            label='Cutoff frequency')
# ax2.hlines(45, 0, np.max(f), colors='r', linestyles='dashed')
# ax2.annotate(f'Cutoff frequency {cutoff(res, cap):.0f} $Hz$',
#             xy=(cutoff(res, cap), 45),
#             xytext=(25, 20),
#             textcoords='offset points',
#             arrowprops=dict(facecolor='black', arrowstyle='->'))

# ax2.set_yticks(np.append(ax2.get_yticks(), [90, 45]))
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

fig.savefig('PE1/session_5/figures/LRC_resonator.pdf')
fig.savefig('PE1/session_5/figures/LRC_resonator.png')
