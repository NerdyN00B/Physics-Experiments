"""A module to control the MyDAQ.

This module provides a class to control the MyDAQ. Specifically allowing the
user to read and write data to the MyDAQ as both seperate tasks, and
simultaneously.

Author: Sam Lamboo
Institution: Leiden University
Student number: s2653346
"""

import nidaqmx as dx
from time import sleep


class MyDAQ():
    """A class to controll the MyDAQ"""
    def __init__(self):
        self.finite = dx.constants.AcquisitionType.FINITE
        pass

    def readWrite(self, write_data, rate=1000, samps=None, read_channel='ai0',
                  write_channel='ao0'):
        """Reads and writes data to the MyDAQ.
        
        parameters
        ----------
        write_data : array
            The voltage data to write to the MyDAQ
        rate : int
            The sample rate in Hz
        samps : int
            The number of samples to read and write. If None, all of write_data
            is written, and the length of write_data is read. If not None, the 
            length of write_data is written and repeated for the ammount of
            samples requested.
        read_channel : str
            The channel to read from
        write_channel : str
            The channel to write to

        returns
        -------
        list
            The data read from the MyDAQ
        """
        with dx.Task('AOTask') as writeTask, dx.Task('AITask') as readTask:
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
            return read_data
    
    def read(self, rate=1000, samps=1000, channel='ai0'):
        """Reads data from the MyDAQ.
        
        parameters
        ----------
        rate : int
            The sample rate in Hz
        samps : int
            The number of samples to read
        channel : str
            The channel to read from
        
        returns
        -------
        list
            The data read from the MyDAQ
        """
        with dx.task() as readTask:
            readTask.ai_channels.add_ai_voltage_chan(f'myDAQ1/{channel}')

            readTask.timing.cfg_samp_clk_timing(rate, sample_mode=self.finite,
                                                samps_per_chan=samps)

            read_data=readTask.read(number_of_samples_per_channel = samps)
            return read_data
        
    def write(self, write_data, rate=1000, samps=None, channel='ao0'):
        """Writes data to the MyDAQ.
        
        parameters
        ----------
        write_data : array
            The voltage data to write to the MyDAQ
        rate : int
            The sample rate in Hz
        samps : int
            The number of samples to write. If None, all of write_data
            is written. If not None, the length of write_data is written and 
            repeated for the ammount of samples requested.
        channel : str
            The channel to write to
        """
        with dx.Task() as writeTask:
            if samps is None:
                samps = len(write_data)
            writeTask.ao_channels.add_ao_voltage_chan(f'myDAQ1/{channel}')
            writeTask.timing.cfg_samp_clk_timing(rate, sample_mode = dx.constants.AcquisitionType.FINITE, samps_per_chan=samps)
            writeTask.write(write_data, auto_start=True)
            sleep(samps/rate + 0.001)
            writeTask.stop()
