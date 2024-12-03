import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from mydaq import MyDAQ
import tkinter as tk
from tkinter import filedialog
import os


def transfer_function(omega, omega_0, q_factor):
    return 1 / (1 - omega**2 / omega_0**2 + 1j * omega / omega_0 / q_factor)


def gain_transfer(omega, omega_0, q_factor, offset):
    # omega *= 2 * np.pi
    return 20 * np.log10(np.abs(transfer_function(omega, omega_0, q_factor))) - offset


def phase_transfer(omega, omega_0, q_factor):
    # omega *= 2 * np.pi
    return np.angle(transfer_function(omega, omega_0, q_factor))


# Values of measurement
samplerate = 200_000
repeat = 3


## Prompt loading and load data
root = tk.Tk()
root.withdraw()

dir = os.getcwd() + '/PE1/session_6'

file_path = filedialog.askopenfilename(filetypes=[('Numpy files', '.npy')],
                                        initialdir=dir,
                                        title='Select data file',
                                        )

data = np.load(file_path)
frequencies = np.load(file_path.replace('.npy', '_frequencies.npy'))
omegas = 2 * np.pi * frequencies

# Analyse data
full_transfer = MyDAQ.get_transfer_functions(data,
                                           frequencies,
                                           repeat=repeat,
                                           samplerate=samplerate,
                                           integration_range=1
                                           )

mean_gain, std_gain, mean_phase, std_phase = MyDAQ.analyse_transfer(full_transfer)

fig, gain_ax, phase_ax, polar_ax = MyDAQ.make_bode_plot(dpi=300,
                                                      layout='tight',
                                                      figsize=(16, 9))

# Plot data

MyDAQ.plot_gain(gain_ax, frequencies, mean_gain, std_gain)
gain_ax.grid(True, which='both')

MyDAQ.plot_phase(phase_ax, frequencies, mean_phase, std_phase)
phase_ax.grid(True, which='both')

MyDAQ.plot_polar(polar_ax, mean_gain, mean_phase)

# # Fit data
# fitplot_freq = np.logspace(np.log10(np.min(frequencies)), np.log10(np.max(frequencies)), 1000)
# popt_gain, pcov_gain = curve_fit(gain_transfer,
#                                  frequencies,
#                                  mean_gain,
#                                  sigma=std_gain,
#                                  p0=[0.8, 10, 50],
#                                  )

# gain_error = np.sqrt(np.diag(pcov_gain))
# gainfit_label = f'Fit: $f_0$ = {popt_gain[0]:.2f} $\pm$ {gain_error[0]:.1e}, Q = {popt_gain[1]:.2f} $\pm$ {gain_error[1]:.1e}'
# gainfit_label += f' offset = {popt_gain[2]:.2f} $\pm$ {gain_error[2]:.1e}'
# # gainfit_label = 'fit'

# popt_phase, pcov_phase = curve_fit(phase_transfer,
#                                    frequencies,
#                                    mean_phase,
#                                    sigma=std_phase,
#                                    p0=[0.8, 10],
#                                    )

# phase_error = np.sqrt(np.diag(pcov_phase))
# phasefit_label = f'Fit: $f_0$ = {popt_phase[0]:.2f} $\pm$ {phase_error[0]:.1e}, Q = {popt_phase[1]:.2f} $\pm$ {phase_error[1]:.1e}'
# # phasefit_label = 'fit'


# gain_ax.plot(fitplot_freq, gain_transfer(fitplot_freq, *popt_gain),
#              'r--', label=gainfit_label)
# gain_ax.legend()

# phase_ax.plot(frequencies, phase_transfer(frequencies, *popt_phase),
#               'r--', label=phasefit_label)
# phase_ax.legend()

fig.savefig(file_path.replace('.npy', '.pdf'))
fig.savefig(file_path.replace('.npy', '.png'))
