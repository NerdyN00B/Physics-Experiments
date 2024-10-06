"""A module to control the MyDAQ.

This module provides a class to control the MyDAQ. Specifically allowing the
user to read and write data to the MyDAQ as both seperate tasks, and
simultaneously.

Parts of this code were inspired by code from Stan, provided by 
Leiden University's PE1 course.

Author: Sam Lamboo
Institution: Leiden University
Student number: s2653346
"""

import numpy as np
import nidaqmx as dx
from time import sleep
from scipy.signal import sawtooth, square


class MyDAQ():
    """A class to controll the MyDAQ"""
    def __init__(self, samplerate: int):
        self.finite = dx.constants.AcquisitionType.FINITE
        self.__samplerate = samplerate

    @property
    def samplerate(self) -> int:
        return self.__samplerate

    @samplerate.setter
    def samplerate(self, new_samplerate: int) -> None:
        assert isinstance(new_samplerate, int), "Samplerate should be an integer."
        assert new_samplerate > 0, "Samplerate should be positive."
        self.__samplerate = new_samplerate

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

    def readWrite(self, write_data, rate=None, samps=None, 
                  read_channel='ai0',
                  write_channel='ao0') -> np.ndarray:
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
                rate = self.__samplerate
                assert rate is not None, "Samplerate should be set first."
            
            if samps is None:
                samps = len(write_data)
            readTask.ai_channels.add_ai_voltage_chan(f'myDAQ1/{read_channel}')
            writeTask.ao_channels.add_ao_voltage_chan(f'myDAQ1/{write_channel}')

            readTask.timing.cfg_samp_clk_timing(rate, sample_mode=self.finite,
                                                samps_per_chan=samps)
            writeTask.timing.cfg_samp_clk_timing(rate, sample_mode=self.finite,
                                                samps_per_chan=samps)

            writeTask.write(write_data, auto_start=True)
            read_data=readTask.read(number_of_samples_per_channel = samps)
            print(read_data)
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
                rate = self.__samplerate
                assert rate is not None, "Samplerate should be set first."
        
        samps = MyDAQ.convertDurationToSamples(rate, duration)

        with dx.Task('readTask') as readTask:
            readTask.ai_channels.add_ai_voltage_chan(f'myDAQ1/{channel}')

            readTask.timing.cfg_samp_clk_timing(rate, sample_mode=self.finite,
                                                samps_per_chan=samps)

            read_data=readTask.read(number_of_samples_per_channel = samps)
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
                rate = self.__samplerate
                assert rate is not None, "Samplerate should be set first."
            
            if samps is None:
                samps = len(write_data)
            writeTask.ao_channels.add_ao_voltage_chan(f'myDAQ1/{channel}')
            writeTask.timing.cfg_samp_clk_timing(rate, sample_mode = dx.constants.AcquisitionType.FINITE, samps_per_chan=samps)
            writeTask.write(write_data, auto_start=True)
            sleep(samps/rate + 0.001)
            writeTask.stop()

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
