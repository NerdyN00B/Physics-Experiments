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
        self.rigol = rm.open_resource(rm.list_resources()[0])

        # Define some constants:
        self.zeroVoltPixel = 124.5  # Acquired by reading out a 0 V DC Signal
        self.verticalDivs = 9  # 8 on the screen, half divs above and below
        self.horizontalDivs = 12  # all on the screen

        # Display constants:
        self.smallestPixel = 11
        self.biggestPixel = 236
        self.timePixels = 600

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

    def flipsignal(self, intdata):
        """Flips the signal so that it corresponds to the RIGOL display. Also convert to numpy"""
        # Flip the signal in intdata around the zero-volt pixel
        flippedSignal = []
        for i in intdata:
            flippedSignal.append(self.zeroVoltPixel - (i - self.zeroVoltPixel))
        flippedSignal = np.array(flippedSignal)
        return flippedSignal

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


class GUI(QMainWindow):
    """Operates the program's Graphical User Interface using PyQt5 and pyqtgraph"""

    def __init__(self):
        super(GUI, self).__init__()  # PyQt5's constructor

        self.configurePyQtGraph()

        # Run the stylesheet:
        uic.loadUi("single_device.ui", self)

        # Start RIGOL connection:
        self.rigol = RigolReader()

        # Initialize the graph:
        self.snapshotGraph = self.snapshotGraph.getPlotItem()
        self.snapshotGraph.plot([0], [0], pen='k')
        self.snapshotGraph.setLabel('left', "Amplitude (V)")
        self.snapshotGraph.setLabel('bottom', "Time (s)")

        # Connect buttons:
        self.snapshotButtonCH1.clicked.connect(self.getDataAndPlotCH1)
        self.snapshotButtonCH2.clicked.connect(self.getDataAndPlotCH2)
        self.snapshotButtonCH12.clicked.connect(self.getDataAndPlotCH12)
        self.browse.clicked.connect(self.getFilePath)
        self.savebutton.clicked.connect(self.savetofile)
        self.show()

        # Class constants:
        self.firstPlot = True
        self.ch1IsPlotted = False
        self.ch2IsPlotted = False

    def getDataAndPlotCH1(self):
        self.time, self.signal = self.rigol.takeSnapshot(ch1=True, ch2=False)
        if self.firstPlot:
            self.snapshotGraph.addLegend()
            self.firstPlot = False
        else:
            try:
                self.snapshotGraph.legend.removeItem("CH 1")
            except Exception as e:
                foo = 1
            try:
                self.snapshotGraph.legend.removeItem("CH 2")
            except Exception as e:
                foo = 1
        self.snapshotGraph.plot(self.time, self.signal, pen=(255, 100, 0), clear=1, name="CH 1")

        self.ch1IsPlotted = True
        self.ch2IsPlotted = False

    def getDataAndPlotCH2(self):
        self.time, self.signal = self.rigol.takeSnapshot(ch1=False, ch2=True)
        if self.firstPlot:
            self.snapshotGraph.addLegend()
            self.firstPlot = False
        else:
            try:
                self.snapshotGraph.legend.removeItem("CH 1")
            except Exception as e:
                foo = 1
            try:
                self.snapshotGraph.legend.removeItem("CH 2")
            except Exception as e:
                foo = 1
        self.snapshotGraph.plot(self.time, self.signal, pen='b', clear=1, name="CH 2")

        self.ch2IsPlotted = True
        self.ch1IsPlotted = False

    def getDataAndPlotCH12(self):
        self.time, self.signal1, self.signal2 = self.rigol.takeSnapshot(ch1=True, ch2=True)
        if self.firstPlot:
            self.snapshotGraph.addLegend()
            self.firstPlot = False
        else:
            try:
                self.snapshotGraph.legend.removeItem("CH 1")
            except Exception as e:
                foo = 1
            try:
                self.snapshotGraph.legend.removeItem("CH 2")
            except Exception as e:
                foo = 1
        self.snapshotGraph.plot(self.time, self.signal1, pen=(255, 100, 0), clear=1, name="CH 1")
        self.snapshotGraph.plot(self.time, self.signal2, pen='b', clear=0, name="CH 2")
        self.ch1IsPlotted = True
        self.ch2IsPlotted = True

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
            if (self.ch1IsPlotted and not self.ch2IsPlotted) or (self.ch2IsPlotted and not self.ch1IsPlotted):
                try:
                    with open(filepath, 'w') as f:
                        print("I\'m writing!")
                        writer = csv.writer(f, delimiter='\t')
                        writer.writerows(zip(self.time, self.signal))
                except PermissionError:
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Warning)
                    msg.setText("Cannot save to file... File is already opened by another program!")
                    msg.exec_()
            elif self.ch2IsPlotted and self.ch1IsPlotted:
                try:
                    with open(filepath, 'w') as f:
                        writer = csv.writer(f, delimiter='\t')
                        writer.writerows(zip(self.time, self.signal1, self.signal2))
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
