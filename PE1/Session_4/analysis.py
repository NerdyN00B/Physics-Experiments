import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.optimize import curve_fit
# filesave dialog
import tkinter as tk
from tkinter import filedialog
import os

def find_nearest_idx(a, value):
    return (np.abs(a - value)).argmin()

def transfer_function(omega, res, cap):
    iwrc = 1j * omega * res * cap
    return iwrc / (1 + iwrc)

def simplified_transfer_function(omega, rescap):
    iwrc = 1j * omega * rescap
    return iwrc / (1 + iwrc)

def gain_function(freq, rescap):
    omega = 2 * np.pi * freq
    return 20 * np.log10(np.abs(simplified_transfer_function(omega, rescap)))

def phase_function(freq, rescap, deg=True):
    omega = 2 * np.pi * freq
    return np.angle(simplified_transfer_function(omega, rescap), deg=deg)

def cutoff(res, cap):
    return 1 / (2 * np.pi * res * cap)

def get_transfer(data_in,
                 data_out,
                 frequencies,
                 samplerate=200_000,
                 integration_range=5,
                 ):
    full_transfer = []
    for i in range(len(data_in)):
        transfer_function = []
        for i, frequency in enumerate(frequencies):
            fourier_in = np.fft.fft(data_in[i])
            fourier_out = np.fft.fft(data_out[i])
            freq = np.fft.fftfreq(len(data_in[i]), 1/samplerate)
            
            idx = find_nearest_idx(freq, frequency)
            integrated_in = np.trapz(fourier_in[idx-integration_range:idx+integration_range],
                                        freq[idx-integration_range:idx+integration_range])
            integrated_out = np.trapz(fourier_out[idx-integration_range:idx+integration_range],
                                        freq[idx-integration_range:idx+integration_range])
            transfer = integrated_out / integrated_in
            
            transfer_function.append(transfer)
        full_transfer.append(np.asarray(transfer_function))
    full_transfer = np.asarray(full_transfer)
    return full_transfer

def gain_plotter(ax, frequencies, gain, gain_error, rescap, rescap_error):
    ax.errorbar(frequencies,
                gain,
                yerr=2*gain_error,
                fmt='ko', 
                label='mean gain $\pm 2\sigma$',)
    ax.plot(frequencies,
            gain_function(frequencies, rescap),
            label=f'fitted gain RC = ({rescap:.2e} $\pm$ {rescap_error:.2e} )$\Omega \cdot F$',
            c='r',
            linestyle='dashed',
            )
    ax.set_xscale('log')
    ax.set_ylabel('Gain [dB]')
    ax.set_xlabel('Frequency [Hz]')
    ax.set_title('Gain transfer function')
    ax.legend()
            
def phase_plotter(ax, frequencies, phase, phase_error, rescap, rescap_error):
    ax.errorbar(frequencies,
                phase,
                yerr=2*phase_error,
                fmt='ko',
                label='mean phase $\pm 2\sigma$',
                )
    ax.plot(frequencies,
            phase_function(frequencies, rescap),
            label=f'fitted phase RC = ({rescap:.2e} $\pm$ {rescap_error:.2e} )$\Omega \cdot F$',
            c='r',
            linestyle='dashed',
            )
    ax.set_xscale('log')
    ax.set_ylabel('Phase [°]')
    ax.set_xlabel('Frequency [Hz]')
    ax.set_title('Phase transfer function')
    ax.legend()

def main():
    cap = 1.5e-9 # F
    res = 1e5 # Ohm
    samplerate = 200_000
    repeat = 4

    root = tk.Tk()
    root.withdraw()

    dir = os.getcwd() + '/PE1/session_3'

    file_path = filedialog.askopenfilename(filetypes=[('Numpy files', '.npy')],
                                            initialdir=dir,
                                            title='Select data file',
                                            )
    
    frequencies = np.load(file_path.replace('.npy', '_frequencies.npy'))
    
    data_in = []
    data_out = []
    for i in range(repeat):
        data = np.load(file_path)
        
        data_in.append(data[0,:,:-samplerate//10]) # remove last 100 ms of data because of readwrite desync
        data_out.append(data[1,:,:-samplerate//10]) # remove last 100 ms of data because of readwrite desync
    
    # Get the transfer function and calculate phase, magniotude and gain
    full_transfer = get_transfer(data_in, data_out, frequencies)
    full_magnitude = np.abs(full_transfer)
    mean_magnitude = np.mean(full_magnitude, axis=0)
    full_gain = 20 * np.log10(full_magnitude)
    full_phase = np.angle(full_transfer, deg=True)
    
    mean_gain = np.mean(full_gain, axis=0)
    std_gain = np.std(full_gain, axis=0)
    mean_phase = np.mean(full_phase, axis=0)
    std_phase = np.std(full_phase, axis=0)
    
    
    # Fit the data
    gain_popt, gain_pcov = curve_fit(gain_function,
                                     frequencies,
                                     mean_gain,
                                     p0=[cap*res],
                                     sigma=std_gain,
                                     absolute_sigma=True,
                                     )
    gain_rescap = gain_popt[0]
    gain_rescap_error = np.sqrt(np.diag(gain_pcov))[0]
    phase_popt, phase_pcov = curve_fit(phase_function,
                                       frequencies,
                                       mean_phase,
                                       p0=[cap*res],
                                       sigma=std_phase,
                                       absolute_sigma=True,
                                       )
    phase_rescap = phase_popt[0]
    phase_rescap_error = np.sqrt(np.diag(phase_pcov))[0]
    
    # Plot the data
    fig = plt.figure(dpi=300, layout='tight', figsize=(16, 9))
    gs = gridspec.GridSpec(2, 2, figure=fig)
    gain_ax = fig.add_subplot(gs[0, 0])
    phase_ax = fig.add_subplot(gs[1, 0])
    polar_ax = fig.add_subplot(gs[:, 1], projection='polar')
    
    gain_plotter(gain_ax,
                 frequencies,
                 mean_gain,
                 std_gain,
                 gain_rescap,
                 gain_rescap_error,
                 )
    gain_ax.text(
        -0.01, 1.1,
        '(a)',
        transform=gain_ax.transAxes,
        fontsize=16,
        fontweight='bold',
        va='top',
        ha='right',
    )
    
    phase_plotter(phase_ax,
                  frequencies,
                  mean_phase,
                  std_phase,
                  phase_rescap,
                  phase_rescap_error,
                  )
    phase_ax.text(
        -0.01, 1.1,
        '(b)',
        transform=phase_ax.transAxes,
        fontsize=16,
        fontweight='bold',
        va='top',
        ha='right',
    )
    
    # Polar plot
    polar_ax.plot(mean_phase, mean_magnitude, 'ko')
    polar_ax.set_title('Polar plot of transfer function')
    polar_ax.text(
        0.1, 1,
        '(c)',
        transform=polar_ax.transAxes,
        fontsize=16,
        fontweight='bold',
        va='top',
        ha='right',
    )

if __name__ == "__main__":
    main()