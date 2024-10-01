import os
import unittest
from functools import wraps
from time import sleep
from typing import List, Optional

import nidaqmx as dx
import numpy as np

from dmm import DMM, DMMHandler, DMM_RIGOL, DMM_TTi
from utils import MeasurementType, MeasurementUnit


def skipIf_no_DMM(method):
    """
    This annotator skips a test if no DMM is present in the DMMTestCase (or the TestCase extending it). This allows us
    to still run other tests that might have nothing to do with a specific DMM.
    """

    @wraps(method)
    def wrapper(self: "DMMTestCase", *args, **kwargs):
        if not (hasattr(self, "dmm") and self.dmm):
            raise unittest.SkipTest("No DMM specified.")
        return method(self, *args, **kwargs)

    return wrapper


def skipIf_TTi(method):
    """
    This annotator skips a test if the DMM under test is a TTi. It is just a garbage device and very hard to test.
    """

    @wraps(method)
    def wrapper(self: "DMMTestCase", *args, **kwargs):
        if isinstance(self.dmm, DMM_TTi):
            raise unittest.SkipTest("Skipping test because it is a TTi.")
        return method(self, *args, **kwargs)

    return wrapper


class DMMTestCase(unittest.TestCase):
    """
    This class provides the base functionality for testing a DMM. We intend to automatically test that we can correctly
    perform the following measurements:
    - AC and DC voltage
    - small AC and DC current
    - large AC and DC current
    - 2- and 4-point resistance measurements

    The tests are carried out by controlling a myDAQ to set AC/DC voltages. To verify the correctness of measurements we
    check that the returned values are within a certain range (tolerance) of the expected value.
    """

    DAQ_SAMPLE_RATE = 200_000  # Hz

    RESISTOR_VALUE = 1000  # Ohm
    RESISTOR_TOLERANCE = 0.02 * RESISTOR_VALUE  # Ohm
    CURRENT_RESISTOR_VALUE = 1000  # Ohm
    CURRENT_RESISTOR_TOLERANCE = 0.02 * CURRENT_RESISTOR_VALUE  # Ohm

    TEST_VOLTAGE_VALUE = 1  # Volt
    TEST_VOLTAGE_TOLERANCE = 0.05 * TEST_VOLTAGE_VALUE  # Volt

    AC_TEST_FREQUENCY = 80  # Hz
    AC_SETTLE_TIME = 0.5  # Seconds

    RMS_CORRECTION_FACTOR = 2 * np.sqrt(2)  # Peak-to-peak = 2 * sqrt(2) * RMS

    DC_VOLTAGE_VALUE = TEST_VOLTAGE_VALUE
    AC_VOLTAGE_VALUE = DC_VOLTAGE_VALUE / RMS_CORRECTION_FACTOR * 2
    DC_CURRENT_VALUE = TEST_VOLTAGE_VALUE / CURRENT_RESISTOR_VALUE
    AC_CURRENT_VALUE = DC_CURRENT_VALUE / RMS_CORRECTION_FACTOR * 2

    DC_VOLTAGE_TOLERANCE = TEST_VOLTAGE_TOLERANCE  # Volt
    AC_VOLTAGE_TOLERANCE = DC_VOLTAGE_TOLERANCE  # Volt
    DC_CURRENT_TOLERANCE = 0.1 * DC_CURRENT_VALUE  # Amperes
    AC_CURRENT_TOLERANCE = 0.1 * DC_CURRENT_VALUE  # Amperes

    DAQ_OUTPUT_IMPEDANCE = 20  # Ohm
    DAQ_OUTPUT_IMPEDANCE_TOLERANCE = 5  # Ohm

    # TTi DMMs are very slow, we need to give them additional time to settle.
    TTi_SETTLE_TIME = 5  # Seconds

    def __init__(self, *args, daq_name: str = "myDAQ1", **kwargs):
        super().__init__(*args, **kwargs)

        self.dmm: Optional[DMM] = None
        self.handler = DMMHandler()

        self.dmm_class = None
        dmm_class_name: Optional[str] = os.environ.get("DMM_CLASS", None)
        if dmm_class_name == "rigol":
            self.dmm_class = DMM_RIGOL
        elif dmm_class_name == "tti":
            self.dmm_class = DMM_TTi
        elif dmm_class_name is not None:
            self.fail(f"Unknown DMM class '{dmm_class_name}'.")

        self.daq_name = daq_name
        self.daq_task: Optional[dx.Task] = None

        # Print all constants from the class so the users knows which values where used.
        print("DMM test constants:")
        for constant_name, value in self.__class__.__dict__.items():
            if constant_name.isupper():
                print(f" - {constant_name}: {value:.2e}")

    def setUp(self) -> None:
        super().setUp()
        self.setUpDMM()
        self.setUpDAQ()

    def setUpDMM(self) -> None:
        if not self.dmm_class:
            return

        # Initialize a new DMM.
        dmm: Optional[DMM] = None
        while not isinstance(dmm, self.dmm_class):
            dmm = self.handler.add_DMM()
            if dmm == 0:
                break

        if not dmm:
            self.fail("Failed to initialize DMM of specified class.")
        self.dmm = dmm

    def setUpDAQ(self) -> None:
        # Create a new task.
        self.daq_task = dx.Task()

        # Register both output channels.
        self.daq_task.ao_channels.add_ao_voltage_chan(f"{self.daq_name}/ao0")
        self.daq_task.ao_channels.add_ao_voltage_chan(f"{self.daq_name}/ao1")

    def tearDown(self) -> None:
        self.tearDownDMM()
        self.tearDownDAQ()
        super().tearDown()

    def tearDownDMM(self) -> None:
        if self.dmm:
            self.dmm.close()
        self.dmm = None

    def tearDownDAQ(self) -> None:
        # Make sure that the output are reset to 0.
        self.write_DAQ_DC([0, 0])
        # Close the task.
        self.daq_task.close()
        # Set the reference to None.
        self.daq_task = None

    def write_DAQ_DC(self, voltage: List[int]) -> None:
        # Stop any previous task to make sure that timings work.
        self.daq_task.stop()
        # Figure out the buffer size so we can appropriately scale the samples, this is done in case timings have been
        # configured. In that case it does not work to write just one file.
        N_samples = self.daq_task.timing.samp_quant_samp_per_chan
        signal = np.array(voltage).repeat(N_samples).reshape(2, N_samples)
        self.daq_task.write(signal, auto_start=True)

    def write_DAQ_AC(self, amplitude: List[int], frequency: float) -> None:
        # Stop any previous task to make sure that timings work.
        self.daq_task.stop()

        N_samples = int(self.DAQ_SAMPLE_RATE / frequency)

        time = np.linspace(0, 1, N_samples).repeat(2).reshape(N_samples, 2).T
        amplitude = np.array(amplitude).repeat(N_samples).reshape(2, N_samples)

        signal = amplitude * np.sin(2 * np.pi * time)

        # Configure timings.
        self.daq_task.timing.cfg_samp_clk_timing(
            self.DAQ_SAMPLE_RATE, sample_mode=dx.constants.AcquisitionType.CONTINUOUS, samps_per_chan=np.long(N_samples)
        )

        # Write the actual signal.
        self.daq_task.write(signal, auto_start=True)

    @skipIf_no_DMM
    def test_DC_voltage(self):
        # We do not care about currents, set it 0. Set the other voltage to the test voltage.
        self.write_DAQ_DC([self.TEST_VOLTAGE_VALUE, 0])

        self.dmm.measurement_type = MeasurementType.VOLTAGE_DC
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        self.assertAlmostEqual(self.DC_VOLTAGE_VALUE, value, delta=self.DC_VOLTAGE_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.VOLT)

    @skipIf_no_DMM
    def test_AC_voltage(self):
        # We do not care about currents, set it 0. Set the other voltage to the test voltage.
        self.write_DAQ_AC([self.TEST_VOLTAGE_VALUE, 0], self.AC_TEST_FREQUENCY)

        self.dmm.measurement_type = MeasurementType.VOLTAGE_AC
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        sleep(self.AC_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        self.assertAlmostEqual(self.AC_VOLTAGE_VALUE, value, delta=self.AC_VOLTAGE_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.VOLT_RMS)

    @skipIf_no_DMM
    def test_DC_small_current(self):
        # We do not care about voltage, set it 0. Set the other voltage to the test voltage.
        self.write_DAQ_DC([0, self.TEST_VOLTAGE_VALUE])

        self.dmm.measurement_type = MeasurementType.SMALL_CURRENT_DC
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        self.assertAlmostEqual(self.DC_CURRENT_VALUE, value, delta=self.AC_CURRENT_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.AMPERE)

    @skipIf_no_DMM
    @skipIf_TTi
    def test_DC_large_current(self):
        # We do not care about voltage, set it 0. Set the other voltage to the test voltage.
        self.write_DAQ_DC([0, self.TEST_VOLTAGE_VALUE])

        self.dmm.measurement_type = MeasurementType.LARGE_CURRENT_DC
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        self.assertAlmostEqual(self.DC_CURRENT_VALUE, value, delta=self.DC_CURRENT_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.AMPERE)

    @skipIf_no_DMM
    def test_AC_small_current(self):
        # We do not care about voltage, set it 0. Set the other voltage to the test voltage.
        self.write_DAQ_AC([0, self.TEST_VOLTAGE_VALUE], self.AC_TEST_FREQUENCY)

        self.dmm.measurement_type = MeasurementType.SMALL_CURRENT_AC
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        sleep(self.AC_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        self.assertAlmostEqual(self.AC_CURRENT_VALUE, value, delta=self.AC_CURRENT_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.AMPERE_RMS)

    @skipIf_no_DMM
    @skipIf_TTi
    def test_AC_large_current(self):
        # We do not care about voltage, set it 0. Set the other voltage to the test voltage.
        self.write_DAQ_AC([0, self.TEST_VOLTAGE_VALUE], self.AC_TEST_FREQUENCY)

        self.dmm.measurement_type = MeasurementType.SMALL_CURRENT_AC
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        sleep(self.AC_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        self.assertAlmostEqual(self.AC_CURRENT_VALUE, value, delta=self.AC_CURRENT_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.AMPERE_RMS)

    @skipIf_no_DMM
    def test_resistance(self):
        # For normal DDMs we simply want to set a voltage on channel 1 so its impedance becomes very large. This trick
        # does not work however for the TTi DDMs, to test those we set the voltage to 0 which then effectively measures
        # the impedance of the MyDAQ instead of the resistor.
        if self.dmm_class == DMM_TTi:
            self.write_DAQ_DC([0, 0])
        else:
            self.write_DAQ_DC([self.TEST_VOLTAGE_VALUE, 0])

        self.dmm.measurement_type = MeasurementType.RESISTANCE_TWO_POINT
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        if self.dmm_class == DMM_TTi:
            self.assertAlmostEqual(self.DAQ_OUTPUT_IMPEDANCE, value, delta=self.DAQ_OUTPUT_IMPEDANCE_TOLERANCE)
        else:
            self.assertAlmostEqual(self.RESISTOR_VALUE, value, delta=self.RESISTOR_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.OHM)

        self.dmm.measurement_type = MeasurementType.RESISTANCE_FOUR_POINT
        if self.dmm_class == DMM_TTi:
            sleep(self.TTi_SETTLE_TIME)
        value, unit = self.dmm.get_data_point()

        self.assertTrue(isinstance(value, float))
        if self.dmm_class == DMM_TTi:
            self.assertAlmostEqual(self.DAQ_OUTPUT_IMPEDANCE, value, delta=self.DAQ_OUTPUT_IMPEDANCE_TOLERANCE)
        else:
            self.assertAlmostEqual(self.RESISTOR_VALUE, value, delta=self.RESISTOR_TOLERANCE)
        self.assertEqual(unit, MeasurementUnit.OHM)


if __name__ == "__main__":
    unittest.main()
