import numpy as np
from mydaq import MyDAQ as md
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
# filesave dialog
import tkinter as tk
from tkinter import filedialog
import os

def find_nearest_idx(a, value):
    return (np.abs(a - value)).argmin()

def transfer_function(frequency, cap, res):
    x_c= 1 / (2 * np.pi * frequency * cap)
    return res / np.sqrt(res**2 + x_c**2)

def db_transfer_function(frequency, cap, res):
    x_c= 1 / (2 * np.pi * frequency * cap)
    return 20*np.log10(res / np.sqrt(res**2 + x_c**2))

def MSD(spectrum, frequencies, cap, res):
    return np.mean((20*np.log10(transfer_function(frequencies, cap, res)) - spectrum)**2)    

def get_spectrum(data, frequencies, samplerate=200_000, amplitude=3):
    """
    Calculate the gain spectrum of the data for a given set of frequencies.
    
    Parameters
    ----------
    data : np.ndarray
        Data array containing the measured data per frequency in frequencies.
    frequencies : np.ndarray
        Array containing the frequencies at which the data was measured.
    samplerate : int, optional
        Samplerate of the data acquisition. The default is 200_000.
    amplitude : int, optional
        Amplitude of the input signal. The default is 3.
    
    Returns
    -------
    np.ndarray
        Array containing the gain of the transfer function at the given
        frequencies.
    """
    spectrum = []
    for i, frequency in enumerate(frequencies):
        fourier = np.fft.fft(data[i])
        freq = np.fft.fftfreq(len(data[i]), 1/samplerate)

        fourier_norm = np.abs(fourier)/len(data[i]) * 2
        idx = find_nearest_idx(freq, frequency)
        deviation = 3

        output_amp = np.trapz(fourier_norm[idx-deviation:idx+deviation],
                              freq[idx-deviation:idx+deviation])
        gain = 20 * np.log10(output_amp/amplitude)
        spectrum.append(gain)
    return np.asarray(spectrum)

def plot_spectrum(spectrum, frequencies, cap, res, theoretical=True):
    """
    Plot the gain spectrum of the transfer function for a given set of frequencies.
    
    Parameters
    ----------
    spectrum : np.ndarray
        Array containing the gain of the transfer function at the given
        frequencies.
    frequencies : np.ndarray
        Array containing the frequencies at which the data was measured.
    cap : float
        Capacitance of the high-pass filter in Farad.
    res : float
        Resistance of the high-pass filter in Ohm.
    
    Returns
    -------
    plt.Figure
        Figure containing the plot of the transfer function.
    plt.Axes
        Axes containing the plot of the transfer function
    """
    fig, ax = plt.subplots(dpi=300, layout='tight')

    ax.semilogx(frequencies,
                spectrum, color='k',
                label='transfer function'
                )    
    ax.hlines(-3,
              np.min(frequencies),
              np.max(frequencies),
              colors='r',
              linestyles='dashed',
              label='$-3 dB$ cutoff'
              )
    
    if theoretical:
        ydata = 20*np.log10(transfer_function(frequencies, cap, res))
        MSD_theoretical = MSD(spectrum, frequencies, cap, res)
        ax.semilogx(frequencies,
                    ydata,
                    color='blue',
                    linestyle='dashed',
                    label=f'theoretical transfer function MSD = {MSD_theoretical:.2e}'
                    )

    ax.set_yticks(np.append(ax.get_yticks(), -3))
    ax.set_xlabel('Frequency $f$ [$Hz$]')
    ax.set_ylabel('Gain [$dB$]')
    ax.set_title('transfer function for high-pass filter')

    ax.grid()
    return fig, ax

def fit(ax, frequencies, spectrum, cap, res):
    popt, pcov = curve_fit(db_transfer_function,
                           frequencies,
                           spectrum,
                           p0=[cap, res])
    
    ydata = 20*np.log10(transfer_function(frequencies, *popt))

    MSD_fit = MSD(spectrum, frequencies, *popt)

    ax.semilogx(frequencies,
                ydata,
                color='orange',
                linestyle='dashed',
                label=f'fitted transfer function MSD = {MSD_fit:.2e}'
                )
    return popt, pcov

if __name__ == "__main__":
    cap = 1.5e-9 # F
    res = 1e5 # Ohm
    samplerate = 200_000

    root = tk.Tk()
    root.withdraw()

    dir = os.getcwd() + '/PE1/session_3'

    file_path = filedialog.askopenfilename(filetypes=[('Numpy files', '.npy')],
                                           initialdir=dir,
                                           title='Select data file',
                                           )
    data = np.load(file_path)
    data = data[:,:-samplerate//10] # remove last 100 ms of data because of readwrite desync
    frequencies = np.load(file_path.replace('.npy', '_frequencies.npy'))

    spectrum = get_spectrum(data, frequencies)

    fig, ax = plot_spectrum(spectrum, frequencies, cap, res)
    popt, pcov = fit(ax, frequencies, spectrum, cap, res)
    ax.legend()
    fig.savefig(file_path.replace('.npy', '_spectrum.pdf'))
    plt.show()

    error = np.sqrt(np.diag(pcov))
    print(f'Capacitance: {popt[0]:.2e} F +/- {error[0]:.2e} F')
    print(f'Resistance: {popt[1]:.2e} Ohm +/- {error[1]:.2e} Ohm')
