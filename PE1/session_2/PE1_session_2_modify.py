import numpy as np
import matplotlib.pyplot as plt
from mydaq import MyDAQ

def main() -> None:
    filename = input("Enter the filename of the signal to be modified: ")
    signal = remove_phase(filename)
    np.save(filename.strip('.npy') + "_phase_removed", signal)

    signal = remove_magnitude(filename)
    np.save(filename.strip('.npy') + "_magnitude_removed", signal)

def remove_phase(filename: str) -> np.ndarray:
    """Remove the phase from a signal.
    
    parameters
    ----------
    filename : str
        The filename of the signal to remove the phase from.
    
    returns
    -------
    np.ndarray
        The signal with the phase removed.
    """
    if filename.endswith("fourier.npy"):
        fourier = np.load(filename)
    else: 
        fourier = np.fft.fft(np.load(filename))

    fourier = np.abs(fourier)
    signal = np.fft.ifft(fourier)
    
    return signal

def remove_magnitude(filename:str) -> np.ndarray:
    """Remove the magnitude from a signal.

    parameters
    ----------
    filename : str
        The filename of the signal to remove the magnitude from.
    
    returns
    -------
    np.ndarray
        The signal with the magnitude removed.
    """
    if filename.endswith("fourier.npy"):
        fourier = np.load(filename)
    else:
        fourier = np.fft.fft(np.load(filename))
    fourier /= np.abs(fourier)
    signal = np.fft.ifft(fourier)
    return signal

if __name__ == "__main__":
    main()