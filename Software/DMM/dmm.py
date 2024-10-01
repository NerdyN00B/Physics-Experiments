import logging
import re
import time
from typing import List, Optional, Tuple

from pyvisa import ResourceManager, VisaIOError
from pyvisa.resources import Resource, SerialInstrument

from utils import MeasurementType, MeasurementUnit


class DMM:
    def __init__(self, instrument: Resource, measurement_type: MeasurementType = MeasurementType.VOLTAGE_DC):
        self.instrument = instrument
        self._measurement_type: MeasurementType = measurement_type

    def close(self):
        self.instrument.close()

    @property
    def measurement_command(self) -> str:
        raise NotImplementedError

    @property
    def measurement_type(self) -> MeasurementType:
        return self._measurement_type

    @measurement_type.setter
    def measurement_type(self, measurement_type: MeasurementType):
        self._measurement_type = measurement_type
        self._update_measurement_type()

    def _update_measurement_type(self):
        self.instrument.write(self.measurement_command)

    def get_fingerprint(self) -> str:
        return self.instrument.query(f"*IDN?{self.instrument.LF}")

    def reset(self):
        raise NotImplementedError

    def get_data_point(self) -> Tuple[float, MeasurementUnit]:
        raise NotImplementedError


class DMM_RIGOL(DMM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.instrument.timeout = 5000
        self.reset()
        self.instrument.write("CMDSET RIGOL")

    @property
    def measurement_command(self) -> str:
        if self.measurement_type == MeasurementType.RESISTANCE_TWO_POINT:
            return ":MEASure:RESistance?"
        elif self.measurement_type == MeasurementType.RESISTANCE_FOUR_POINT:
            return ":MEASure:FRESistance?"
        elif self.measurement_type == MeasurementType.VOLTAGE_DC:
            return "MEASure:VOLTage:DC?"
        elif self.measurement_type == MeasurementType.VOLTAGE_AC:
            return "MEASure:VOLTage:AC?"
        elif (
                self.measurement_type == MeasurementType.SMALL_CURRENT_DC
                or self.measurement_type == MeasurementType.LARGE_CURRENT_DC
        ):
            return "MEASure:CURRent:DC?"
        elif (
                self.measurement_type == MeasurementType.SMALL_CURRENT_AC
                or self.measurement_type == MeasurementType.LARGE_CURRENT_AC
        ):
            return "MEASure:CURRent:AC?"
        raise ValueError

    def reset(self):
        self.instrument.write("*RST")
        time.sleep(1)

    def get_data_point(self):
        datapoint = float(self.instrument.query(self.measurement_command))
        return datapoint, self.measurement_type.unit


class DMM_SIGLENT(DMM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.instrument.timeout = 5000
        self.reset()

    @property
    def measurement_command(self) -> str:
        if self.measurement_type == MeasurementType.RESISTANCE_TWO_POINT:
            return "CONF:RES"
        elif self.measurement_type == MeasurementType.RESISTANCE_FOUR_POINT:
            return "CONF:FRES"
        elif self.measurement_type == MeasurementType.VOLTAGE_DC:
            return "CONF:VOLT:DC"
        elif self.measurement_type == MeasurementType.VOLTAGE_AC:
            return "CONF:VOLT:AC"
        elif (
                self.measurement_type == MeasurementType.SMALL_CURRENT_DC
                or self.measurement_type == MeasurementType.LARGE_CURRENT_DC
        ):
            return "CONF:CURR:DC"
        elif (
                self.measurement_type == MeasurementType.SMALL_CURRENT_AC
                or self.measurement_type == MeasurementType.LARGE_CURRENT_AC
        ):
            return "CONF:CURR:AC"
        raise ValueError

    def reset(self):
        self.instrument.write("*RST")
        time.sleep(1)
        self._update_measurement_type()

    def get_data_point(self):
        datapoint = float(self.instrument.query("READ?"))
        return datapoint, self.measurement_type.unit


class DMM_TTi(DMM):
    def __init__(self, *args, **kwargs):
        """
        Initialize RIGOL DMM with the given VISA resource number and initialize it
        in the given measurement_type.
        """
        super().__init__(*args, **kwargs)

        self.instrument.baud_rate = 9600
        self.instrument.read_termination = b"\x0A"
        self.instrument.timeout = 5000

        self.instrument.flush(16)

        self.instrument.write_raw(b"\x02\x0A")
        self.reset()

        self.measurement_type = self._measurement_type

    def get_fingerprint(self) -> str:
        self.set_to_listen()
        self.instrument.write("*IDN?\n")
        self.set_to_talk()
        return self.instrument.read_raw().decode("utf-8")

    @property
    def measurement_command(self) -> str:
        if (
                self.measurement_type == MeasurementType.RESISTANCE_TWO_POINT
                or self.measurement_type == MeasurementType.RESISTANCE_FOUR_POINT
        ):
            return "OHMS\n"
        elif self.measurement_type == MeasurementType.VOLTAGE_DC:
            return "VDC\n"
        elif self.measurement_type == MeasurementType.VOLTAGE_AC:
            return "VAC\n"
        elif self.measurement_type == MeasurementType.SMALL_CURRENT_DC:
            return "ADC\n"
        elif self.measurement_type == MeasurementType.LARGE_CURRENT_DC:
            return "A10DC\n"
        elif self.measurement_type == MeasurementType.SMALL_CURRENT_AC:
            return "AAC\n"
        elif self.measurement_type == MeasurementType.LARGE_CURRENT_AC:
            return "A10AC\n"
        raise ValueError

    @DMM.measurement_type.setter
    def measurement_type(self, measurement_type: MeasurementType):
        self._measurement_type = measurement_type

        self.set_to_listen()
        self.instrument.write(self.measurement_command)
        self.instrument.write("AUTO\n")
        time.sleep(0.1)

    def set_to_listen(self):
        """Set multimeter in listening mode"""
        self.instrument.write_raw(b"\x12")  # set listening addres
        self.instrument.write_raw(b"A")  # for adress 1
        self.instrument.write_raw(b"\x0A")  # close command

        # check for acknowledge signal (\x06)
        response = self.instrument.read_bytes(1)
        if response != b"\x06":
            raise IOError("Unexpected response. Expected acknowledge signal")

    def set_to_talk(self):
        """Ask for response from multimeter"""
        self.instrument.write_raw(b"\x14")  # set talking addres
        self.instrument.write_raw(b"A")  # for adress 1
        self.instrument.write_raw(b"\x0A")  # close command

    def reset(self):
        # Reset the DMM
        self.set_to_listen()
        self.instrument.write("*RST\n")
        time.sleep(1)

    def get_data_point(self):
        # Ask the TTi to do a measurement_type
        self.set_to_listen()
        self.instrument.write("READ?\n")
        self.set_to_talk()

        try:
            result = self.instrument.read_bytes(18)  # read result
            bytestringvalue = result[:11].decode("UTF-8")

            if bytestringvalue == " +OVERLOAD ":
                datapoint = 20e3
            elif bytestringvalue == " -OVERLOAD ":
                datapoint = 0
            else:
                datapoint = float(bytestringvalue)
        except Exception as e:
            print(f"Exception occurred whilst obtaining data from DMM {e}")
            # If the datapoint is not a float or could not be retrieved.
            datapoint = 0.0

        if (
                self.measurement_type == MeasurementType.SMALL_CURRENT_DC
                or self.measurement_type == MeasurementType.SMALL_CURRENT_AC
                or self.measurement_type == MeasurementType.LARGE_CURRENT_DC
                or self.measurement_type == MeasurementType.LARGE_CURRENT_AC
        ):
            # TTi DMM returns value in mAmp(rms).
            datapoint /= 1000
        elif (
                self.measurement_type == MeasurementType.RESISTANCE_TWO_POINT
                or self.measurement_type == MeasurementType.RESISTANCE_FOUR_POINT
        ):
            # TTi DMM returns value in kOhm
            datapoint *= 1000

        return datapoint, self.measurement_type.unit


class DMMHandler:
    RIGOL_DM3058E_FINGERPRINT = re.compile(r"Rigol Technologies,DM3058E,[A-Z\d]+,(?:\d{2}.){5}\d{2}\n")
    SIGLENT_SDM3055_FINGERPRINT = re.compile(r"Siglent Technologies,SDM3055,SDM[A-Z\d]+,\d.\d{2}.\d{2}.\d{2}(R\d)?\n")
    TTI_1906_FINGERPRINT = re.compile(r"THURLBY-THANDAR,1906,0,\d+.\d+\r\n")

    def __init__(self):
        self.dmms: List[DMM, ...] = []  # array which holds the DMM's in use.

    def add_DMM(self, measurement_type: MeasurementType = MeasurementType.VOLTAGE_DC):
        """
        Initialize a new DMM with the given VISA resource number and add it to the list of DMMs in use.
        """

        available_resources = self.get_available_resource_names()

        # Loop through all available resource names and add this DMM
        for resource_name in available_resources:
            try:
                dmm = self.initialize_DMM(resource_name, measurement_type)
            except VisaIOError as e:
                logging.warning(f"Unable to connect to device: {e}")
                continue
            return dmm
        logging.warning("No DMM found")
        return None

    def initialize_DMM(self, resource_name: str, measurement_type: MeasurementType) -> Optional[DMM]:
        """
        Initialize a DMM with the given VISA resource number and initialize this DMM with the given measurement_type
        """
        resource_manager = ResourceManager()

        try:
            instrument = resource_manager.open_resource(resource_name)
        except VisaIOError as e:
            logging.warning(f"Failed to instantiate DMM with resource name {resource_name}: {e}")
            return None

        if isinstance(instrument, SerialInstrument):
            # We are dealing with an ancient TTi 1906 computing multimeter, delegate to the appropriate class.
            dmm = DMM_TTi(instrument, measurement_type)
        else:
            # To determine which class to use, we need to fingerprint the resource.
            fingerprint = instrument.query(f"*IDN?{instrument.LF}")
            if self.RIGOL_DM3058E_FINGERPRINT.match(fingerprint):
                dmm = DMM_RIGOL(instrument, measurement_type)
            elif self.SIGLENT_SDM3055_FINGERPRINT.match(fingerprint):
                dmm = DMM_SIGLENT(instrument, measurement_type)
            else:
                logging.warning(f"Failed to identify fingerprint: {fingerprint}")
                return None

        logging.info(f"Initialized DMM with resource name {resource_name}")
        self.dmms.append(dmm)
        return dmm

    @staticmethod
    def get_connected_resource_names() -> Tuple[str, ...]:
        """
        Return a list of all connected VISA resource numbers.
        """
        resource_manager = ResourceManager()
        available_resources = resource_manager.list_resources()
        logging.debug(f"Connected resources: {available_resources}")
        return available_resources

    def get_used_resource_names(self) -> Tuple[str, ...]:
        """
        Return a list of all VISA resource numbers which are already in use.
        """
        used_resource_names = [dmm.instrument._resource_name for dmm in self.dmms]
        # When a USB resource is connected, an additional number is added to the resource name. We need to get rid of
        # it. See https://pyvisa.readthedocs.io/en/1.8/names.html.
        for i, used_resource_name in enumerate(used_resource_names):
            if used_resource_name.startswith("USB"):
                used_resource_names[i] = re.sub(r":\d+:", "", used_resource_name)
        logging.debug(f"Used resources: {used_resource_names}")
        return tuple(used_resource_names)

    def get_available_resource_names(self) -> Tuple[str, ...]:
        """
        Return a list of all available VISA resource numbers which are not already in use.
        """
        connected_resources = self.get_connected_resource_names()
        used_resource_names = self.get_used_resource_names()

        available_resource_names = tuple(set(connected_resources) - set(used_resource_names) - {"ASRL1::INSTR"})
        logging.debug(f"Available resources: {available_resource_names}")
        return available_resource_names

    def remove_DMM(self, dmm: DMM):
        """
        Close the given DMM and remove it from the list of DMMs in use.
        """
        dmm.close()
        self.dmms.remove(dmm)
