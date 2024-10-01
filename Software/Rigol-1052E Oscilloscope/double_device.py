"""
@author M.Rog
@date 19 November 2018
Program takes a snapshot from a RIGOL 1000E series oscilloscope using visa.
Includes option to save the snapshot to hard drive.
Dependencies: Visa, PyQt5, pyqtgraph"""

import csv
import sys

import numpy as np
import pyqtgraph as pg
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox
from pyvisa import ResourceManager


class RigolReader(object):
    """Operates connection with Rigol, allowing this object to take snapshots from the Rigol's screen"""

    def __init__(self):
        """Establishes connection"""
        rm = ResourceManager()
        self.rigols = [rm.open_resource(rm.list_resources()[0]), rm.open_resource(rm.list_resources()[1])]
        print(self.rigols)

        # Define some constants:
        self.zeroVoltPixel = 124.5  # Acquired by reading out a 0 V DC Signal
        self.verticalDivs = 9  # 8 on the screen, half divs above and below
        self.horizontalDivs = 12  # all on the screen

        # Display constants:
        self.smallestPixel = 11
        self.biggestPixel = 236
        self.timePixels = 600

    def readscales(self, chan, device):
        """Calibrates the axes of the RIGOL"""
        self.voltPerDiv = np.float64(self.rigols[device].query(":CHAN" + str(chan) + ":SCAL?"))
        self.timePerDiv = np.float64(self.rigols[device].query(":TIM:SCAL? CHAN" + str(chan)))
        self.voltOffset = np.float64(self.rigols[device].query(":CHAN" + str(chan) + ":OFFS?"))

    def rawsignal(self, chan, device):
        """Get unchanged data from the screen, throw away junk and return this data"""
        self.rigols[device].write(":WAVeform:DATA? CHAN" + str(chan))  # command to request data
        data = self.rigols[device].read_raw()  # read data (read raw reads bytes)
        intdata = np.array(list(data))[10:]
        return intdata

    def flipsignal(self, intdata):
        """Flips the signal so that it corresponds to the RIGOL display. Also convert to numpy"""
        # Flip the signal in intdata around the zero-volt pixel
        flippedSignal = []
        for i in intdata:
            flippedSignal.append(self.zeroVoltPixel - (i - self.zeroVoltPixel))
        flippedSignal = np.array(flippedSignal)
        return flippedSignal

    def takeSnapshot(self):
        """Takes snapshot from the Rigol"""
        timeAxes = []
        voltAxes = []
        for device in range(0, 2):
            for chan in range(1, 3):
                self.readscales(chan, device)
                rawsignal = self.rawsignal(chan, device)
                time, signal = self.prettify_rawdata(rawsignal)
                timeAxes.append(time)
                voltAxes.append(signal)
        return timeAxes, voltAxes

    def prettify_rawdata(self, rawdata):
        """Uses set parameters to convert raw data to time+volt axes."""
        flippedSignal = self.flipsignal(rawdata)
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
        voltAxis = (flippedSignal - offsetZeroVoltPixel) * voltsPerPixel

        return timeAxis, voltAxis


class GUI(QMainWindow):
    """Operates the program's Graphical User Interface using PyQt5 and pyqtgraph"""

    def __init__(self):
        super(GUI, self).__init__()  # PyQt5's constructor

        self.configurePyQtGraph()

        # Run the stylesheet:
        uic.loadUi("double_device.ui", self)

        # Start RIGOL connection:
        self.rigol = RigolReader()

        # Initialize the graph:
        self.snapshotGraph = self.snapshotGraph.getPlotItem()
        self.snapshotGraph.plot([0], [0], pen='k')
        self.snapshotGraph.setLabel('left', "Amplitude (V)")
        self.snapshotGraph.setLabel('bottom', "Time (s)")

        # Connect buttons:
        self.snapshotButtonAllChannels.clicked.connect(self.getDataAndPlot)
        self.browse.clicked.connect(self.getFilePath)
        self.savebutton.clicked.connect(self.savetofile)
        self.show()

        # Class constants:
        self.firstPlot = True

    def getDataAndPlot(self):
        self.times, self.signals = self.rigol.takeSnapshot()
        if self.firstPlot:
            self.snapshotGraph.addLegend()
            self.firstPlot = False
        else:
            self.snapshotGraph.legend.removeItem("CH 1.1")
            self.snapshotGraph.legend.removeItem("CH 1.2")
            self.snapshotGraph.legend.removeItem("CH 2.1")
            self.snapshotGraph.legend.removeItem("CH 2.2")
        self.snapshotGraph.plot(self.times[0], self.signals[0], pen=(255, 100, 0), clear=1, name="CH 1.1")
        self.snapshotGraph.plot(self.times[1], self.signals[1], pen='b', clear=0, name="CH 1.2")
        self.snapshotGraph.plot(self.times[2], self.signals[2], pen='r', clear=0, name="CH 2.1")
        self.snapshotGraph.plot(self.times[3], self.signals[3], pen='g', clear=0, name="CH 2.2")

    def configurePyQtGraph(self):
        """Sets PyQtGraph settings"""
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        pg.setConfigOptions(antialias=True)

    def getFilePath(self):
        """Gets file path from file browser and puts it into the text field"""
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "",
                                                  "All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            self.filepath.setText(fileName)
            return fileName
        return ""

    def savetofile(self):
        filepath = self.filepath.text()
        if filepath == "":
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("Cannot save to file... No filepath was set.")
            msg.exec_()
        else:
            try:
                with open(filepath, 'w') as f:
                    print("I\'m writing!")
                    writer = csv.writer(f, delimiter='\t')
                    writer.writerows(zip(self.times[0], self.signals[0], self.times[1], self.signals[1], self.times[2],
                                         self.signals[2], self.times[3], self.signals[3]))
            except PermissionError:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Cannot save to file... File is already opened by another program!")
                msg.exec_()


def __main__():
    """Runs the program's main loop"""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    window = GUI()
    app.exec_()


sys.exit(__main__())
