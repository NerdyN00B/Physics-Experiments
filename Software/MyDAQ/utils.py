from typing import List

import nidaqmx as dx

def get_available_mydaq_devices() -> List[str]:
    """
    Returns a list of all available MyDAQ devices. These can be used directly to create a new output channel in a
    dx.Task object.
    """
    devices = dx.system.System.local().devices
    device_names = [str(device).split("=")[1].split(")")[0] for device in devices]
    return list(sorted(device_names))
