import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from mydaq import MyDaq
import tkinter as tk
from tkinter import filedialog
import os

def lrc_transfer(omega, omega_0, q_factor):
    w0 = omega_0
    Q = q_factor
    return 1 / (1 - (omega / w0)**2 + 1j * omega / (w0 * Q))

def omega_0(inductance, capacitance):
    return 1 / np.sqrt(inductance * capacitance)

def q_factor(resistance, inductance, capacitance):
    return 1 / resistance * np.sqrt(inductance / capacitance)

def gain_transfer(omega, omega_0, q_factor):
    return 20 * np.log10(lrc_transfer(omega, omega_0, q_factor))

def phase_transfer(omega, omega_0, q_factor):
    return np.angle(lrc_transfer(omega, omega_0, q_factor))

## Values of components
cap = 50e-9
res = 500
ind = 100e-3
samplerate = 200_000
repeat = 5

## Prompt loading and load data
root = tk.Tk()
root.withdraw()

dir = os.getcwd() + '/PE1/session_5'

file_path = filedialog.askopenfilename(filetypes=[('Numpy files', '.npy')],
                                        initialdir=dir,
                                        title='Select data file',
                                        )

data = np.load(file_path)
frequencies = np.load(file_path.replace('.npy', '_frequencies.npy'))

data = data[:, :, :, :samplerate//10]

# Analyse data
full_transfer = MyDaq.get_transfer_functions(data,
                                           frequencies,
                                           repeat=repeat,
                                           samplerate=samplerate,
                                           integration_range=5,
                                           )

mean_gain, std_gain, mean_phase, std_phase = MyDaq.analyse_transfer(full_transfer)

fig, gain_ax, phase_ax, polar_ax = MyDaq.make_bode_plot(dpi=300,
                                                      layout='tight',
                                                      figsize=(16, 9))

## Plot and fit
# gain plot
MyDaq.plot_gain(gain_ax, frequencies, mean_gain, std_gain)
popt_gain, pcov_gain = curve_fit(gain_transfer,
                                 frequencies,
                                 mean_gain,
                                 p0=[omega_0(ind, cap),
                                     q_factor(res, ind, cap)],
                                 sigma=std_gain,
                                 absolute_sigma=True,
                                 )
gain_fit = gain_ax.plot(frequencies,
                        gain_transfer(frequencies, *popt_gain),
                        'r--')

error_gain_fit = np.sqrt(np.diag(pcov_gain))

gain_label = f'Gain fit: $\omega_0$ = ({popt_gain[0]:.2f}'
gain_label += f' $\pm$ {error_gain_fit[0]:.2f}) Hz, '
gain_label += f'$Q$ = {popt_gain[1]:.2f} $\pm$ {error_gain_fit[1]:.2f}'

gain_fit.set_label(gain_label)

gain_ax.vlines(popt_gain[0], np.min(mean_gain), np.max(mean_gain),
               colors='r', linestyles='dashed',
               label='Resonance frequency from fit')

gain_ax.legend()
gain_ax.grid()

# phase plot
MyDaq.plot_phase(phase_ax, frequencies, mean_phase, std_phase)
popt_phase, pcov_phase = curve_fit(phase_transfer,
                                   frequencies,
                                   mean_phase,
                                   p0=[omega_0(ind, cap),
                                       q_factor(res, ind, cap)],
                                   sigma=std_phase,
                                   absolute_sigma=True,
                                   )
phase_fit = phase_ax.plot(frequencies,
                          phase_transfer(frequencies, *popt_phase),
                          'r--')

error_phase_fit = np.sqrt(np.diag(pcov_phase))

phase_label = f'Phase fit: $\omega_0$ = ({popt_phase[0]:.2f}'
phase_label += f' $\pm$ {error_phase_fit[0]:.2f}) Hz, '
phase_label += f'$Q$ = {popt_phase[1]:.2f} $\pm$ {error_phase_fit[1]:.2f}'

phase_fit.set_label(phase_label)

phase_ax.vlines(popt_phase[0], np.min(mean_phase), np.max(mean_phase),
                colors='r', linestyles='dashed',
                label='Resonance frequency from fit')

phase_ax.legend()
phase_ax.grid()

# polar plot
MyDaq.plot_polar(polar_ax, mean_gain, mean_phase)

fig.savefig(file_path.replace('.npy', '.pdf'))