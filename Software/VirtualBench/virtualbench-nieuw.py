"""
See README.md for more information. This software allows you to interface with the VirtualBench 8012 series.

Authors:
- Matthijs Rog <rog@physics.leidenuniv.nl>
- Julian van Doorn <j.c.b.van.doorn@umail.leidenuniv.nl>
- Bálint Bosman <bbosman@physics.leidenuniv.nl>
"""

import sys
import os
import time
import numpy as np
from pyvirtualbench import PyVirtualBench

# Check if we are running 32-bit.
if sys.maxsize > 2**32:
    raise Exception(
        "The pyvirtualbench library is only compatible with 32-bit Python. You can find the 32-bit "
        "version at C:/Python32/python32.exe. Use a Command Prompt to run the 32-bit version of Python."
    )


class VirtualBench8012:
    def __init__(self, serial_number: str):
        self.serial_number = f"VB8012-{serial_number}"
        self.virtual_bench = PyVirtualBench(self.serial_number)
        self.mixed_signal_oscilloscope = self.virtual_bench.acquire_mixed_signal_oscilloscope()
        self.mixed_signal_oscilloscope.auto_setup()
        self.sample_rate = self.acquisition_time = self.pretrigger_time = None

    def configure(self, sample_rate, acquisition_time, pretrigger_time, expected_amplitude):
        self.mixed_signal_oscilloscope.configure_timing(sample_rate, acquisition_time, pretrigger_time, 0)
        self.sample_rate, self.acquisition_time, self.pretrigger_time, _ = self.mixed_signal_oscilloscope.query_timing()
        self.mixed_signal_oscilloscope.configure_analog_channel(
            self.serial_number + "/mso/1", True, expected_amplitude, 0, 1, 1
        )
        self.mixed_signal_oscilloscope.configure_digital_edge_trigger(self.serial_number + "/trig", 1, 0)

        print(
            f"Configured: \nsample-rate =  {self.sample_rate} Hz\n"
            f"acquisition time = {self.acquisition_time} s\n"
            f"pre-trigger time = {self.pretrigger_time} s. \n "
        )

    def __call__(self):
        self.mixed_signal_oscilloscope.run(False)
        data, *_ = self.mixed_signal_oscilloscope.read_analog_digital_u64()
        self.mixed_signal_oscilloscope.stop()
        return data


if __name__ == "__main__":
    print("VirtualBench High-Speed Readout Software")
    print("========================================")
    print(
        "This program takes a snapshot from a VirtualBench 8012 series oscilloscope using pyvirtualbench.\n"
        "Includes option to save the snapshot to hard drive.\n"
        "\n"
        "Please keep in mind that channel 1 is the only channel that can be used for this program.\n"
        "The maximum sample rate is 1 GS/s and at most 1M samples can be taken at a time.\n"
        "\n"
        "Note: for unknown reasons, some sample rates / measurement times are not allowed.\n"
        "Note: measurements start after a trigger signal (TRIG). \n A small voltage pulse should work, for example (dis)connecting a cable. \n"
    )

    # Get the serial number of the VirtualBench 8012.
    serial_number = input("Enter the serial number of the VirtualBench 8012 > ")
    virtual_bench = VirtualBench8012(serial_number)

    sample_rate = 500_000_000
    sample_rate = float(input(f"Enter the sample rate (Hz) or press [ Return ] to select [ default = {sample_rate} ] > ") or sample_rate)
    acquisition_time = 1e-3
    acquisition_time = float(input(f"Enter Acquisition time (s) or press [ Return ] to select [ default = {acquisition_time} ] > ") or acquisition_time)
    pretrigger_time = 1e-9
    pretrigger_time = float(input(f"Enter Pre-trigger time (s) or press [ Return ] to select [ default = {pretrigger_time} ] > ") or acquisition_time)
    expected_amplitude = 1
    expected_amplitude = float(
        input(f"Enter Expected expected_amplitude (V) or press [ Return ] to select [ default = {expected_amplitude}] > ") or expected_amplitude
    )
    print('\n')

    # Initialize the VirtualBench 8012.

continue_measuring = True



while continue_measuring:
        print("Initializing...")
        virtual_bench.configure(sample_rate, acquisition_time, pretrigger_time, expected_amplitude)

        # Take a snapshot.
        print("Waiting for trigger voltage on TRIG...")
        data = virtual_bench()
        time_arr = np.linspace(0, virtual_bench.acquisition_time, len(data))
        time_versus_voltage = np.vstack((time_arr, data)).T
        print("Finished measuring. Starting save ...")


        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = "vbdata-" + timestr + ".csv"

        path = "P:/Virtualbench_Data"
        filepath = path + "/" + filename

        if not os.path.exists(path):
            # Create the directory
            os.makedirs(path)
            print("Made a new directory to save: " + path)
        else:
            pass

        np.savetxt(filepath, time_versus_voltage)
        print("saved at: " + filepath)


        want_to_continue = input("continue with new measurement? [y/n]  > ")
        if want_to_continue == "y":
            continue_measuring = True 
        else:
            continue_measuring = False

print('Goodbye')

