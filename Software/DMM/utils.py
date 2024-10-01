from enum import Enum, auto
from typing import List

import nidaqmx as dx


class MeasurementUnit(Enum):
    OHM = auto()

    VOLT = auto()
    VOLT_RMS = auto()

    AMPERE = auto()
    AMPERE_RMS = auto()

    def __str__(self):
        """
        Simply convert the name to lowercase and replace underscores with spaces.

        Examples:
            MeasurementUnit.OHM -> "ohm"
            MeasurementUnit.VOLT_RMS -> "volt rms"
        """
        return self.name.lower().replace("_", " ")


class MeasurementType(Enum):
    RESISTANCE_TWO_POINT = auto()
    RESISTANCE_FOUR_POINT = auto()

    VOLTAGE_DC = auto()
    VOLTAGE_AC = auto()

    SMALL_CURRENT_DC = auto()
    SMALL_CURRENT_AC = auto()

    LARGE_CURRENT_DC = auto()
    LARGE_CURRENT_AC = auto()

    def __str__(self):
        return self.name.lower().replace("_", " ")

    @property
    def unit(self) -> MeasurementUnit:
        """
        Returns the corresponding unit for the measurement_type type.
        """
        if self == MeasurementType.RESISTANCE_TWO_POINT or self == MeasurementType.RESISTANCE_FOUR_POINT:
            return MeasurementUnit.OHM
        elif self == MeasurementType.VOLTAGE_DC:
            return MeasurementUnit.VOLT
        elif self == MeasurementType.VOLTAGE_AC:
            return MeasurementUnit.VOLT_RMS
        elif self == MeasurementType.SMALL_CURRENT_DC or self == MeasurementType.LARGE_CURRENT_DC:
            return MeasurementUnit.AMPERE
        elif self == MeasurementType.SMALL_CURRENT_AC or self == MeasurementType.LARGE_CURRENT_AC:
            return MeasurementUnit.AMPERE_RMS
        raise ValueError("No unit is defined for this measurement_type.")


def get_available_mydaq_devices() -> List[str]:
    """
    Returns a list of all available MyDAQ devices. These can be used directly to create a new output channel in a
    dx.Task object.
    """
    devices = dx.system.System.local().devices
    device_names = [str(device).split("=")[1].split(")")[0] for device in devices]
    return device_names
