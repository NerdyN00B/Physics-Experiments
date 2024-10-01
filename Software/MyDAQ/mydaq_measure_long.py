import nidaqmx as dx
import numpy as np
import time
import matplotlib.pyplot as plt

from utils import get_available_mydaq_devices

chunksize = 100

class MyDAQ_Long():
	def __init__(self):
		self.data = []
		
		
	def capture(self, duration=10, samplerate=1000):
		"""Captures input of Ai0 for duration seconds at samplerate samplerate."""
		self.data = [] # Clear data
		
		self.task = dx.Task()

		available_devices = get_available_mydaq_devices()
		selected_device = available_devices[0] if available_devices else "myDAQ1"
		print(f"Attempting to use {selected_device}.")

		self.task.ai_channels.add_ai_voltage_chan(f"{selected_device}/ai0")
		self.task.timing.cfg_samp_clk_timing(samplerate,sample_mode=dx.constants.AcquisitionType.CONTINUOUS)
		self.task.register_every_n_samples_acquired_into_buffer_event(chunksize, self.updateData)
		self.task.start()
		time.sleep(duration+0.01)
		self.task.stop()
	
		return np.linspace(0, duration, len(np.array(self.data).flatten())), np.array(self.data).flatten()
		
	def updateData(self, task_handle, every_n_samples_event_type, number_of_samples, callback_data):
		newdata = self.task.read(number_of_samples_per_channel=chunksize)
		self.data.append(newdata)
		return 0
	