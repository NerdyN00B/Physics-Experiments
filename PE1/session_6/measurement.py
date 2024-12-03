import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from mydaq import MyDAQ
import tkinter as tk
from tkinter import filedialog
import os


def transfer_function(omega, omega_0, q_factor):
    return 1 / (1 - omega**2 / omega_0**2 + 1j * omega / omega_0 / q_factor)


def gain_transfer(omega, omega_0, q_factor):
    return 20 * np.log10(transfer_function(omega, omega_0, q_factor))


def phase_transfer(omega, omega_0, q_factor):
    return np.angle(transfer_function(omega, omega_0, q_factor))


## Prompt save file
dir = os.getcwd()
dir += '/PE1/session_6'

root = tk.Tk()
root.withdraw()

savefile = filedialog.asksaveasfilename(filetypes=[('Numpy files', '.npy')],
                                         defaultextension='.npy',
                                         initialdir=dir,
                                         title='Save raw data as',
                                         confirmoverwrite=True,
                                         )


# Start of the measurement code
repeat = 3

daq = MyDAQ(200_000, 'myDAQ3')

frequencies = np.linspace(0.6, 1, 15)

data = daq.measure_spectrum(frequencies,
                            duration=10,
                            amplitude=10,
                            repeat=repeat,
                            )

# Save data
np.save(savefile, data)
np.save(savefile.replace('.npy', '_frequencies.npy'), frequencies)

# Analyse data
full_transfer = daq.get_transfer_functions(data,
                                           frequencies,
                                           repeat=repeat,
                                           samplerate=daq.samplerate,
                                           integration_range=1
                                           )

mean_gain, std_gain, mean_phase, std_phase = daq.analyse_transfer(full_transfer)

fig, gain_ax, phase_ax, polar_ax = daq.make_bode_plot(dpi=300,
                                                      layout='tight',
                                                      figsize=(16, 9))

# Plot data

daq.plot_gain(gain_ax, frequencies, mean_gain, std_gain)
gain_ax.grid(True, which='both')

daq.plot_phase(phase_ax, frequencies, mean_phase, std_phase)
phase_ax.grid(True, which='both')

daq.plot_polar(polar_ax, mean_gain, mean_phase)

# Fit data
# fitplot_freq = np.logspace(-0.5, 1, 1000)
# popt_gain, pcov_gain = curve_fit(gain_transfer,
#                                  frequencies,
#                                  mean_gain,
#                                  sigma=std_gain,
#                                  p0=[0.8, 10],
#                                  )

# gain_error = np.sqrt(np.diag(pcov_gain))
# gainfit_label = f'Fit: $\omega_0$ = {popt_gain[0]:.2f} $\pm$ {gain_error[0]:.1e}, Q = {popt_gain[1]:.2f} $\pm$ {gain_error[1]:.1e}'

# popt_phase, pcov_phase = curve_fit(phase_transfer,
#                                    frequencies,
#                                    mean_phase,
#                                    sigma=std_phase,
#                                    p0=[0.8, 10],
#                                    )

# phase_error = np.sqrt(np.diag(pcov_phase))
# phasefit_label = f'Fit: $\omega_0$ = {popt_phase[0]:.2f} $\pm$ {phase_error[0]:.1e}, Q = {popt_phase[1]:.2f} $\pm$ {phase_error[1]:.1e}'


# gain_ax.plot(fitplot_freq, gain_transfer(fitplot_freq, *popt_gain),
#              'r--', label=gainfit_label)
# gain_ax.legend()

# phase_ax.plot(fitplot_freq, phase_transfer(fitplot_freq, *popt_phase),
#               'r--', label=phasefit_label)
# phase_ax.legend()

fig.savefig(savefile.replace('.npy', '.pdf'))
fig.savefig(savefile.replace('.npy', '.png'))