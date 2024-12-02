"""A module to control the MyDAQ.

This module provides a class to control the MyDAQ. Specifically allowing the
user to read and write data to the MyDAQ as both seperate tasks, and
simultaneously.

Parts of this code were inspired or modified from the mydaqclass code made by 
Stan, provided by Leiden University's PE1 course.

Author: Sam Lamboo
Institution: Leiden University
Student number: s2653346
"""

import numpy as np
import nidaqmx as dx
from time import sleep
from scipy.signal import sawtooth, square
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

class MyDAQ():
    """A class to controll the MyDAQ"""
    def __init__(self, samplerate: int, name: str='myDAQ2'):
        self.finite = dx.constants.AcquisitionType.FINITE
        self.__samplerate = samplerate
        self.__name = name

    @property
    def samplerate(self) -> int:
        return self.__samplerate

    @samplerate.setter
    def samplerate(self, new_samplerate: int) -> None:
        assert isinstance(new_samplerate, int), "Samplerate should be an integer."
        assert new_samplerate > 0, "Samplerate should be positive."
        self.__samplerate = new_samplerate
    
    @property
    def name(self) -> str:
        return self.__name
    
    @name.setter
    def name(self, new_name: str) -> None:
        assert isinstance(new_name, str), "Name should be a string."
        self.__name = new_name

    @staticmethod
    def convertDurationToSamples(samplerate: int, duration: float) -> int:
        samples = duration * samplerate

        # Round down to nearest integer
        return int(samples)

    @staticmethod
    def convertSamplesToDuration(samplerate: int, samples: int) -> float:
        duration = samples / samplerate

        return duration

    @staticmethod
    def getTimeArray(duration: float, samplerate: int) -> np.ndarray:
        steps = MyDAQ.convertDurationToSamples(samplerate, duration)
        return np.linspace(1 / samplerate, duration, steps)
    
    def _addOutputChannels(self, 
                           task: dx.task.Task, 
                           channels
                           ) -> None:
        """Add output channels to the DAQ
        
        parameters
        ----------
        task : dx.task.Task
            The task to add the channels to
        channels : str | list[str]
            The channels to add to the task
        """
        assert not (self.name is None), "Name should be set first."

        # Make sure channels can be iterated over
        if isinstance(channels, str):
            channels = [channels]

        # Iterate over all channels and add to task
        for channel in channels:
            if self.name in channel:
                task.ao_channels.add_ao_voltage_chan(channel)
            else:
                task.ao_channels.add_ao_voltage_chan(f"{self.name}/{channel}")

    def _addInputChannels(self, 
                          task: dx.task.Task, 
                          channels
                          ) -> None:
        """Add input channels to the DAQ
        
        parameters
        ----------
        task : dx.task.Task
            The task to add the channels to
        channels : str | list[str]
            The channels to add to the task
        """
        assert not (self.name is None), "Name should be set first."

        # Make sure channels can be iterated over
        if isinstance(channels, str):
            channels = [channels]

        # Iterate over all channels and add to task
        for channel in channels:
            if self.name in channel:
                task.ai_channels.add_ai_voltage_chan(channel)
            else:
                task.ai_channels.add_ai_voltage_chan(f"{self.name}/{channel}")

    def _configureChannelTimings(self, task: dx.task.Task, samples: int) -> None:
        """Set the correct timings for task based on number of samples
        
        parameters
        ----------
        task : dx.task.Task
            The task to set the timing for
        samples : int
            The number of samples to read or write
        """
        assert not (self.samplerate is None), "Samplerate should be set first."

        task.timing.cfg_samp_clk_timing(
            self.samplerate,
            sample_mode=self.finite,
            samps_per_chan=samples,
        )

    def readWrite(self, write_data, rate=None, samps=None, 
                  read_channel='ai0',
                  write_channel='ao0'
                  ) -> np.ndarray:
        """Reads and writes data to the MyDAQ.
        
        parameters
        ----------
        write_data : array
            The voltage data to write to the MyDAQ
        rate : int
            The sample rate in Hz, if None take from class attribute
        samps : int
            The number of samples to read and write. If None, all of write_data
            is written, and the length of write_data is read. If not None, the 
            length of write_data is written and repeated for the ammount of
            samples requested.
        read_channel : str
            The channel to read from, default is 'ai0'
        write_channel : str
            The channel to write to, default is 'ao0'

        returns
        -------
        np.ndarray
            The data read from the MyDAQ
        """
        with dx.Task('AOTask') as writeTask, dx.Task('AITask') as readTask:
            if rate is None:
                rate = self.samplerate
                assert rate is not None, "Samplerate should be set first."
            
            if samps is None:
                samps = len(write_data)
            
            self._addOutputChannels(writeTask, write_channel)
            self._addInputChannels(readTask, read_channel)
            
            # readTask.ai_channels.add_ai_voltage_chan(f'{self.name}/{read_channel}')
            # writeTask.ao_channels.add_ao_voltage_chan(f'{self.name}/{write_channel}')

            self._configureChannelTimings(readTask, samps)
            self._configureChannelTimings(writeTask, samps)
            # readTask.timing.cfg_samp_clk_timing(rate, sample_mode=self.finite,
            #                                     samps_per_chan=samps)
            # writeTask.timing.cfg_samp_clk_timing(rate, sample_mode=self.finite,
            #                                     samps_per_chan=samps)

            writeTask.write(write_data, auto_start=True)
            read_data = readTask.read(number_of_samples_per_channel = samps)
            
            writeTask.stop()
            return np.asarray(read_data)

    def read(self, duration: float, rate=None, channel='ai0') -> np.ndarray:
        """Reads data from the MyDAQ.
        
        parameters
        ----------
        rate : int
            The sample rate in Hz, if None take from class attribute
        duration : float
            The duration in seconds to read data for
        channel : str
            The channel to read from, default is 'ai0'
        
        returns
        -------
        np.ndarray
            The data read from the MyDAQ
        """
        if rate is None:
                rate = self.samplerate
                assert rate is not None, "Samplerate should be set first."
        
        samps = MyDAQ.convertDurationToSamples(rate, duration)

        with dx.Task('readTask') as readTask:
            self._addInputChannels(readTask, channel)
            self._configureChannelTimings(readTask, samps)

            read_data = readTask.read(number_of_samples_per_channel = samps)
            return np.asarray(read_data)

    def write(self, write_data, rate=None, samps=None, channel='ao0') -> None:
        """Writes data to the MyDAQ.
        
        parameters
        ----------
        write_data : array
            The voltage data to write to the MyDAQ
        rate : int
            The sample rate in Hz, if None take from class attribute
        samps : int
            The number of samples to write. If None, all of write_data
            is written. If not None, the length of write_data is written and 
            repeated for the ammount of samples requested.
        channel : str
            The channel to write to
        """
        with dx.Task() as writeTask:
            if rate is None:
                rate = self.samplerate
                assert rate is not None, "Samplerate should be set first."
            
            if samps is None:
                samps = len(write_data)
            
            self._addOutputChannels(writeTask, channel)
            self._configureChannelTimings(writeTask, samps)
            
            writeTask.write(write_data, auto_start=True)
            sleep(samps/rate + 0.001)
            writeTask.stop()
    
    def measure_spectrum(self,
                         frequencies,
                         duration: float =1,
                         amplitude: float =3,
                         repeat: int =1,
                         write_channel: str ='ao0',
                         read_input_channel: str ='ai0',
                         read_output_channel: str ='ai1',
                         ):
        """Measure over a spectrum of frequencies.
        
        parameters
        ----------
        frequencies : np.ndarray
            The frequencies to measure at
        duration : float
            The duration of the measurement per frequency
        amplitude : float
            The amplitude of the waveform
        repeat : int
            The number of times to measure per frequency
        write_channel : str
            The channel to write the waveform to
        read_input_channel : str
            The channel to read the original input from (straight from the 
            output to this channel for later comparison)
        read_output_channel : str
            The channel to read the output of the system from
        
        returns
        -------
        np.ndarray
            The measured data,
            on the first axis, index 0 is the input data, index 1 is the output
            data. On the second axis, the index corresponds to repeat. On the
            third axis, the index corresponds to the frequency as provided.
        """
        assert isinstance(repeat, int), "Repeat should be an integer."
        assert repeat > 0, "Repeat should be a positive integer."
        
        input_data = []
        output_data = []
        
        for _ in range(repeat):
            input_data_i = []
            output_data_i = []
            
            for frequency in frequencies:
                waveform = self.generateWaveform('sine',
                                                 self.samplerate,
                                                 frequency,
                                                 amplitude,
                                                 duration=duration
                                                 )[1]
                
                read = self.readWrite(waveform,
                                      read_channel=[read_input_channel,
                                                    read_output_channel],
                                      write_channel=write_channel
                                      )
                
                input_data_i.append(read[0])
                output_data_i.append(read[1])
            
            input_data.append(np.asarray(input_data_i))
            output_data.append(np.asarray(output_data_i))
        
        if repeat == 1:
            return np.stack((np.asarray(input_data_i),
                             np.asarray(output_data_i)))
        else:
            return np.stack((np.asarray(input_data),
                             np.asarray(output_data)))

    @staticmethod
    def get_transfer_functions(
        data: np.ndarray,
        frequencies,
        repeat: int = 1,
        samplerate: int = 200_000,
        integration_range: int = 0,
        ) -> np.ndarray:
        """Analyse the spectrum of a measured dataset.
        
        parameters
        ----------
        data : np.ndarray
            The measured data, like provided by measure_spectrum
        frequencies : np.ndarray
            The frequencies measured at
        repeat : int
            The number of times the measurement was repeated
        samplerate : int
            The samplerate of the measurement
        integration_range : int
            How many points to integrate over left and right from the assumed
            peak. [idx-integratin_range:idx+integration_range] is integrated.
        
        returns
        -------
        np.ndarray
            The transfer function(s) of the system
        """
        assert isinstance(repeat, int), "Repeat should be an integer."
        assert repeat > 0, "Repeat should be a positive integer."
        
        full_transfer = []
        for i in range(repeat):
            transfer_function = []
            for j, frequency in enumerate(frequencies):
                fourier_in = np.fft.fft(data[0][i][j])
                fourier_out = np.fft.fft(data[1][i][j])
                freq = np.fft.fftfreq(len(data[0][i][j]), 1/samplerate)
                
                if integration_range == 0:
                    idx = MyDAQ.find_nearest_idx(freq, frequency)
                    transfer = fourier_out[idx] / fourier_in[idx]
                    transfer_function.append(transfer)
                    continue
                else:
                    idx = MyDAQ.find_nearest_idx(freq, frequency)
                    integrated_in = np.trapz(fourier_in[idx-integration_range:idx+integration_range],
                                            freq[idx-integration_range:idx+integration_range])
                    
                    integrated_out = np.trapz(fourier_out[idx-integration_range:idx+integration_range],
                                            freq[idx-integration_range:idx+integration_range])
                
                transfer = integrated_out / integrated_in
                
                transfer_function.append(transfer)
            
            full_transfer.append(np.asarray(transfer_function))
        
        if repeat == 1:
            return np.asarray(transfer_function)
        else:
            return np.asarray(full_transfer)
        
    @staticmethod
    def analyse_transfer(transfer_functions: np.ndarray, isgain=True):
        """Analyse the transfer functions of a system.
        
        parameters
        ----------
        transfer_functions : np.ndarray
            The transfer functions of the system
        isgain : bool
            Whether to analyse the gain or the magnitude
        
        returns
        -------
        mean_gain/magnitude : np.ndarray
            The mean gain/magnitude of the transfer functions
        std_gain/magnitude : np.ndarray
            The standard deviation of the gain/magnitude of the transfer
            functions
        mean_phase : np.ndarray
            The mean phase of the transfer functions in radians
        std_phase : np.ndarray
            The standard deviation of the phase of the transfer functions in
            radians
        """
        magnitude = np.abs(transfer_functions)
        gain = 20 * np.log10(magnitude)
        phase = np.angle(transfer_functions)
        
        mean_magnitude = np.mean(gain, axis=0)
        std_magnitude = np.std(gain, axis=0)
        
        mean_gain = np.mean(gain, axis=0)
        std_gain = np.std(gain, axis=0)
        
        mean_phase = np.mean(phase, axis=0)
        std_phase = np.std(phase, axis=0)
        
        if isgain:
            return mean_gain, std_gain, mean_phase, std_phase
        else:
            return mean_magnitude, std_magnitude, mean_phase, std_phase
    
    @staticmethod
    def make_bode_plot(**kwargs):
        """Create a bodeplot figure.
        
        parameters
        ----------
        **kwargs
            Additional keyword arguments for plt.figure
        
        returns
        -------
        fig : plt.Figure
            The figure
        gain_ax : plt.Axes
            The axis for the gain plot
        phase_ax : plt.Axes
            The axis for the phase plot
        polar_ax : plt.Axes
            The axis for the polar plot
        """
        fig = plt.figure(**kwargs)
        gs = gridspec.GridSpec(2, 2, figure=fig)
        
        gain_ax = fig.add_subplot(gs[0, 0])
        phase_ax = fig.add_subplot(gs[1, 0])
        polar_ax = fig.add_subplot(gs[:, 1], projection='polar')
        
        return fig, gain_ax, phase_ax, polar_ax
        
    
    @staticmethod
    def plot_gain(ax: plt.Axes,
                  frequencies,
                  gain,
                  gain_error,
                  fmt = 'ok',
                  capsize = 2,
                  label = 'mean gain $\pm 2\sigma$',
                  **kwargs) -> None:
        """Plot the gain of a system.
        
        parameters
        ----------
        ax : plt.Axes
            The axis to plot on
        frequencies : np.ndarray
            The frequencies measured at
        gain : np.ndarray
            The gain of the transfer function
        gain_error : np.ndarray
            The error on the gain of the transfer function
        **kwargs
            Additional keyword arguments for ax.errorbar function
        """
        ax.errorbar(frequencies, gain, yerr=gain_error, fmt=fmt,
                    label=label, capsize=capsize, **kwargs)
        
        ax.set_xscale('log')
        ax.set_ylabel('Gain [dB]')
        ax.set_xlabel('Frequency [Hz]')
        ax.set_title('Gain transfer function')
    
    @staticmethod
    def plot_phase(ax: plt.Axes,
                   frequencies,
                   phase,
                   phase_error,
                   deg=True,
                   fmt = 'ok',
                   capsize = 2,
                   label = 'mean phase $\pm 2\sigma$',
                   **kwargs) -> None:
        """Plot the phase of a system.
        
        parameters
        ----------
        ax : plt.Axes
            The axis to plot on
        frequencies : np.ndarray
            The frequencies measured at
        phase : np.ndarray
            The phase of the transfer function
        phase_error : np.ndarray
            The error on the phase of the transfer function
        deg : bool
            Whether to convert the phase to degrees
        **kwargs
            Additional keyword arguments for ax.errorbar function
        """
        if deg:
            phase = np.rad2deg(phase)
            phase_error = np.rad2deg(phase_error)
        
        ax.errorbar(frequencies, phase, yerr=phase_error, fmt=fmt,
                    label=label, capsize=capsize, **kwargs)
        
        ax.set_xscale('log')
        ax.set_ylabel('Phase [°]')
        ax.set_xlabel('Frequency [Hz]')
        ax.set_title('Phase transfer function')
    
    @staticmethod
    def plot_polar(ax: plt.Axes,
                   gain: np.ndarray,
                   phase: np.ndarray,
                   magnitude=False,
                   color = 'k',
                   **kwargs):
        """Make polar plot of transfer function.
        
        if magnitude is True, gain is interpreted as magnitude. Otherwise gain
        is interpreted as dB and magnitude is calculated from gain.
        """
        if not magnitude:
            magnitude = 10**(gain/20)
        else: 
            magnitude = gain
        
        ax.scatter(phase, magnitude, color=color, **kwargs)
        ax.set_title('Polar plot of transfer function')
    
    @staticmethod
    def find_nearest_idx(a, value):
        return (np.abs(a - value)).argmin()

    @staticmethod
    def generateWaveform(
        function,
        samplerate: int,
        frequency: float,
        amplitude: float = 1,
        phase: float = 0,
        duration: float = 1,
        phaseInDegrees: bool = True,
    ) -> np.ndarray:
        """
        Geneate a waveform from the 4 basic wave parameters

        Parameters
        ----------
        function : str or callable
            Type of waveform. The parameters `amplitude`, `frequency` and 
            `phase` are passed to the callable.
        samplerate: int
            Samplerate with which to sample waveform.
        frequency : int or float
            Frequency of the waveform.
        amplitude : int or float, optional
            Amplitude of the waveform in volts. The default is 1.
        phase : int or float, optional
            Phase of the waveform. The default is 0. In degrees if
            faseinDegrees is True. Otherwise in radians.
        duration : int or float, optional
            Duration of the waveform in seconds. The default is 1.
        phaseInDegrees: bool, optional
            Whether phase is given in degrees. The default is True.

        Returns
        -------
        timeArray : ndarray
            ndarray containing the discrete times at which the waveform is evaluated.
        wave : ndarray
            ndarray of the evaluated waveform.

        """
        timeArray = MyDAQ.getTimeArray(duration, samplerate)
        if phaseInDegrees:
            phase = np.deg2rad(phase)

        if not callable(function):
            function = MyDAQ.findFunction(function)

        wave = function(timeArray, amplitude, frequency, phase)

        return timeArray, wave

    @staticmethod
    def findFunction(function: str):
        """Find a function to generate simple continuous waveforms.

        parameters
        ----------
        function : str
            The name of the function to generate

        returns
        -------
        function : function
            The function corresponding to the name.
        """
        if function == "sine":
            return lambda x, A, f, p: A * np.sin(2 * np.pi * f * x + p)
        if function == "cosine":
            return lambda x, A, f, p: A * np.cos(2 * np.pi * f * x + p)
        elif function == "square":
            return lambda x, A, f, p: A * square(2 * np.pi * f * x + p)
        elif function == "sawtooth":
            return lambda x, A, f, p: A * sawtooth(2 * np.pi * f * x + p)
        elif function == "isawtooth":
            return lambda x, A, f, p: A * sawtooth(2 * np.pi * f * x + p,
                                                   width=0)
        elif function == "triangle":
            return lambda x, A, f, p: A * sawtooth(2 * np.pi * f * x + p,
                                                   width=0.5)
        else:
            raise ValueError(f"{function} is not a recognized wavefront form")
