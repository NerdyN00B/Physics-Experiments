"""
@author M.Rog
@date 19 November 2018
Program takes a snapshot from a RIGOL 1000E series oscilloscope using visa.
Includes option to save the snapshot to hard drive.
Dependencies: Visa"""

import numpy as np
from pyvisa import ResourceManager


class RigolOscilloscope(object):
    """Controls the connection with Rigol, allowing this object to take snapshots from the Rigol's screen"""

    def __init__(self):
        """Establishes connection"""
        rm = ResourceManager()
        self.rigol = rm.open_resource(rm.list_resources()[0])

        # Define some constants:
        self.zeroVoltPixel = 124.5  # Acquired by reading out a 0 V DC Signal
        self.verticalDivs = 9  # 8 on the screen, half divs above and below
        self.horizontalDivs = 12  # all on the screen

        # Display constants:
        self.smallestPixel = 11
        self.biggestPixel = 236
        self.timePixels = 600

    def captureChannel1(self):
        return self.takeSnapshot(ch1=True)

    def flipsignal(self, intdata):
        """Flips the signal so that it corresponds to the RIGOL display. Also convert to numpy"""
        # Flip the signal in intdata around the zero-volt pixel
        flippedSignal = []
        for i in intdata:
            flippedSignal.append(self.zeroVoltPixel - (i - self.zeroVoltPixel))
        flippedSignal = np.array(flippedSignal)
        return flippedSignal

    def readscales(self, chan):
        """Calibrates the axes of the RIGOL"""
        self.voltPerDiv = np.float64(self.rigol.query(":CHAN" + str(chan) + ":SCAL?"))
        self.timePerDiv = np.float64(self.rigol.query(":TIM:SCAL? CHAN" + str(chan)))
        self.voltOffset = np.float64(self.rigol.query(":CHAN" + str(chan) + ":OFFS?"))

    def rawsignal(self, chan):
        """Get unchanged data from the screen, throw away junk and return this data"""
        self.rigol.write(":WAVeform:DATA? CHAN" + str(chan))  # command to request data
        data = self.rigol.read_raw()  # read data (read raw reads bytes)
        intdata = np.array(list(data))[10:]
        return intdata

    def takeSnapshot(self, ch1=True, ch2=False):
        """Takes snapshot from the Rigol"""
        # Channel 1:
        if ch1:
            self.readscales(1)  # Calibrate the axes
            rawsignal = self.rawsignal(1)
            flippedSignal = self.flipsignal(rawsignal)
            # Now scale the data
            # Find volts per pixel;
            totalAmountOfPixels = self.biggestPixel - self.smallestPixel
            totalAmountOfVolts = self.verticalDivs * self.voltPerDiv
            voltsPerPixel = totalAmountOfVolts / totalAmountOfPixels

            # Find the offsetted zero pixel
            offsetZeroVoltPixel = self.zeroVoltPixel + self.voltOffset / voltsPerPixel

            # Now scale the time axis
            timePerPixel = (self.timePerDiv * self.horizontalDivs) / self.timePixels
            timeAxis = np.arange(0, self.timePixels, 1) * timePerPixel
            voltSignalCH1 = (flippedSignal - offsetZeroVoltPixel) * voltsPerPixel

        if ch2:
            self.readscales(2)  # Calibrate the axes
            rawsignal = self.rawsignal(2)
            flippedSignal = self.flipsignal(rawsignal)
            # Now scale the data
            # Find volts per pixel;
            totalAmountOfPixels = self.biggestPixel - self.smallestPixel
            totalAmountOfVolts = self.verticalDivs * self.voltPerDiv
            voltsPerPixel = totalAmountOfVolts / totalAmountOfPixels

            # Find the offsetted zero pixel
            offsetZeroVoltPixel = self.zeroVoltPixel + self.voltOffset / voltsPerPixel

            # Now scale the time axis
            timePerPixel = (self.timePerDiv * self.horizontalDivs) / self.timePixels
            timeAxis = np.arange(0, self.timePixels, 1) * timePerPixel
            voltSignalCH2 = (flippedSignal - offsetZeroVoltPixel) * voltsPerPixel

        if ch1 and not ch2:
            return timeAxis, voltSignalCH1
        if not ch1 and ch2:
            return timeAxis, voltSignalCH2
        if ch1 and ch2:
            return timeAxis, voltSignalCH1, voltSignalCH2
