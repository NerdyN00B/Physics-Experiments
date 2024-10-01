"""
AlphalasGUI.py
Developed by Koen J.M. Schouten

ALPHALAS GUI
	v1.1

	Leiden Institute of Physics, Leiden University. Bachelorlab TOO department.
    Email: TOO@physics.leidenuniv.nl.

	This program is free software: you can redistribute it and/or modify it under 
    the terms of the GNU General Public License as published by the Free Software 
    Foundation, either version 3 of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
    without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with this program. 
    If not, see <https://www.gnu.org/licenses/>.

	This Python code contains a Graphical User Interface for retrieving data from the CCD-2000-D(-UV) or CCD-S3600-D(-UV) device.

	PYTHON INSTRUCTIONS:
	The example code works with Python version 3.7 or higher. Earlier versions may also work, but have not been tested.
    This code requires the the following libraries to be installed: PyQT5, numpy, sys, os, pyqtgraph. Also, the
    AlphalasCCD class is required, which should be included along with this file.
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PyQt5 import uic
import numpy as np
import sys
import os
import pyqtgraph as pg
from TOO_AlphalasCCD import AlphalasCCD

pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'g')
pg.setConfigOptions(antialias=True)

class AlphalasGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        #Open ui file with same name as current file
        uifilename = __file__[:-2]+"ui"
        uic.loadUi(uifilename, self)

        self.alphalasCCD = 0
        self.isMeasuring = 0
        
        #This disables some notification about the integration time of the CCD-2000
        self.integrationTimeNote.setVisible(False)      

        #Set a timer such that the timer is updated 24/sec
        self.CCDtimer = pg.QtCore.QTimer()
        self.CCDtimer.setInterval(int(1000/24))
        self.CCDtimer.timeout.connect(self.updateData)
        
        self.setupPlots()
        self.connectUI()
        self.show()

    def setupPlots(self):
        #Sets up all plot information.
        self.zoomBounds = [800,1200]

        self.plotItemAll=self.plotWidgetall.getPlotItem() # This plot contains all data 
        self.plotItemAll.plot(pen='g')
        self.plotItemAll.setLabels(bottom ='Pixel ', left= 'Signal', title= 'CCD')
        self.curveall = self.plotItemAll.plot(pen='g')
        self.plotItemAll.disableAutoRange(axis = 1)
        self.gridall = pg.GridItem()
        self.plotWidgetall.addItem(self.gridall)
        self.lr = pg.LinearRegionItem(self.zoomBounds,bounds = [0,4000],brush = pg.hsvColor(0,1,.66,alpha = 0.4)) # used for the zoom
        self.plotWidgetall.addItem(self.lr)

        self.plotItemZoom=self.plotWidgetzoom.getPlotItem() # This plot contains only the zoom in
        self.plotItemZoom.plot(pen='r')
        self.plotItemZoom.setLabels(bottom ='Pixel ', left= 'Signal', title= 'CCD Slice')
        self.curvezoom = self.plotItemZoom.plot(pen='r')
        self.plotItemZoom.disableAutoRange(axis = 1)
        self.gridzoom = pg.GridItem()
        self.plotWidgetzoom.addItem(self.gridzoom)
        self.cursor1 = pg.InfiniteLine(900,movable = True,pen = 'y')
        self.cursor2 = pg.InfiniteLine(1100,movable = True)#,pen = 'g')
        self.plotWidgetzoom.addItem(self.cursor1)
        self.plotWidgetzoom.addItem(self.cursor2)

    def connectUI(self):
        #Connect the UI elements to functions

        self.SelectPathButton.clicked.connect(self.selectPath)
        self.SaveButton.clicked.connect(self.saveData)
        self.StartButton.clicked.connect(self.initializeMeasurement)
        self.StopButton.clicked.connect(self.stopMeasuring)
        self.t_int.valueChanged.connect(self.updateIntegrationTime)
        self.shots_per_acq.valueChanged.connect(self.updateShotsPerAcquisition)
        self.lr.sigRegionChanged.connect(self.updateZoom)

        self.cursor1.sigPositionChanged.connect(lambda: self.updateCursor(self.cursor1, self.cursor1Pos, 1))
        self.cursor2.sigPositionChanged.connect(lambda: self.updateCursor(self.cursor2, self.cursor2Pos, 1))
        self.cursor1Pos.valueChanged.connect(lambda: self.updateCursor(self.cursor1, self.cursor1Pos, 0))
        self.cursor2Pos.valueChanged.connect(lambda: self.updateCursor(self.cursor2, self.cursor2Pos, 0))

    def initializeMeasurement(self):
        #Initialize the measurememt by connecting the CCD
        
        if not self.isMeasuring:
            self.alphalasCCD = AlphalasCCD() #Connect the CCD

            if not self.alphalasCCD.device:
                self.showError("Could not find a CCD-2000-D or CCD-3600S-D connected to the computer. \nPlease check the USB connection with the device!", QMessageBox.Warning)
            else:
                self.updateIntegrationTime()
                self.updateShotsPerAcquisition()
                
                array_size = self.alphalasCCD.getArraySize()

                #Update the axis and zoombounds of the graph. Needed because the
                # 2000-D and S3600-D have different array sizes.
                self.xdata = np.arange(array_size)
                self.zoomBounds = [int(array_size / 2) - 200, int(array_size / 2) + 200]
                self.lr.setRegion(self.zoomBounds)
                self.cursor1.setValue(self.zoomBounds[0] + 100)
                self.cursor2.setValue(self.zoomBounds[1] - 100)

                self.isMeasuring = 1
                self.CCDtimer.start()
        else:
            print("We were already measuring!")

    def updateGraph(self):
        #Updates the graph widget

        if len(self.data) > 0:
            Vmin = float(0)
            Vmax = float(self.VmaxEdit.currentText())

            #Set the range of the displayed signal
            self.plotWidgetall.setRange(yRange=[Vmin,Vmax])
            self.plotWidgetzoom.setRange(yRange=[Vmin,Vmax])
            try:
                #Update the datapoints in the graph.
                self.curveall.setData(self.xdata,self.data)
                self.curvezoom.setData(self.xdata[int(self.zoomBounds[0]):int(self.zoomBounds[1])],self.data[int(self.zoomBounds[0]):int(self.zoomBounds[1])])
                self.plotWidgetzoom.setXRange(self.zoomBounds[0],self.zoomBounds[1])
            except Exception:
                pass
            #Update the values displayed on the cursos.
            self.cursor1Sig.setText(str(self.data[int(self.cursor1.value())-1]))
            self.cursor2Sig.setText(str(self.data[int(self.cursor2.value())-1]))

    def updateData(self):
        #Read the data and update the graph
        self.data = self.alphalasCCD.readoutData()
        self.updateGraph()
    
    def stopMeasuring(self):
        #Stop the measurement and close the communication ports
        if self.isMeasuring:
            self.alphalasCCD.closeDevice()
            self.alphalasCCD = 0
            self.isMeasuring = 0
            self.CCDtimer.stop()
        else:
            print("we were already stopped!")         

    def updateIntegrationTime(self):
        #Updates the integration time
        inttime = self.t_int.value()
        
        #Make the note on the integrationtime visible for low integration times
        if inttime < 5000:
            self.integrationTimeNote.setVisible(True)
        else:
            self.integrationTimeNote.setVisible(False)
        
        if self.alphalasCCD:
            self.alphalasCCD.updateSetting("integration_time", inttime)

    def updateShotsPerAcquisition(self):
        #Updates the number of shots per acquisition
        shots = self.shots_per_acq.value()
        if self.alphalasCCD:
            self.alphalasCCD.updateSetting("shots_per_acquisition", shots)
        
    def updateZoom(self):
        #Updates the zoom screen. Also moves the cursors if they would fall outside the zoom window
        self.zoomBounds = self.lr.getRegion()

        self.cursor1.setValue(max(self.cursor1.value(), min(self.zoomBounds)))
        self.cursor1.setValue(min(self.cursor1.value(), max(self.zoomBounds)))
        self.cursor2.setValue(max(self.cursor2.value(), min(self.zoomBounds)))
        self.cursor2.setValue(min(self.cursor2.value(), max(self.zoomBounds)))

    def updateCursor(self, cursor, cursorPos, cursorChanged):
        #Update the text value (cursor position) if cursor position (text value) changed
        if cursorChanged: 
            cursorPos.setValue(int(cursor.value()))
        else:
            cursor.setValue(int(cursorPos.value()))

    def selectPath(self):
        self.SaveDirectoryText.setText(QFileDialog.getExistingDirectory())

    def saveData(self):
        """
        Saves the current data and time arrays to a file
        """
        #Tranpose the array to get the data in columns
        try:
            dataArray = np.array([self.xdata,self.data]).transpose()
        except:
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("No data to save.")
            errormsg.exec_()
            return

        savePath = self.SaveDirectoryText.toPlainText()
        saveName = self.FileName.toPlainText()
        extension = ".csv" #standard extension

        if savePath == 'P:/':
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("Data not saved! No permission to write directly to the P: disk. Please save your data in a subfolder.")
            errormsg.exec_()

            return 0

        #Check if saveName format is correct, also check for extension
        splitSaveName = saveName.split('.')
        if len(splitSaveName) == 2:
            extension = "." + splitSaveName[1] 
        if not saveName or len(splitSaveName) > 2:
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("Data not save because of invalid filename!")
            errormsg.exec_()
            return
        
        saveName = splitSaveName[0]

        #Check if file already exists.
        if self.doesFileExist(savePath + '/' + saveName + extension):
            i = 1
            while self.doesFileExist(savePath + '/' + saveName + "(" + str(i) + ")" + extension): i += 1

            #Put the number (i) behind the save name to not override old files
            saveName = saveName + "(" + str(i) + ")"
            
        dest = "{}".format(savePath) + "/{}".format(saveName)

        try:
            np.savetxt(dest + extension, dataArray, delimiter = ",", header = "Pixel, Signal")
            savemsg = QMessageBox()
            savemsg.setIcon(QMessageBox.Information)
            savemsg.setText("Data Saved!")
            savemsg.exec_()
        except PermissionError:
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("Data not saved! No permission to write in that folder.")
            errormsg.exec_()
        except OSError:
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("Data not saved! Provide a valid path (by clicking on the button) and a valid filename")
            errormsg.exec_()
        # Catch a save error.

    def doesFileExist(self, name):
        """
        Checks if there already exists a file named name in the current directory.
        - name is a string with the name of the file, e.g. "Foo.txt".
        - Returns True if it already does exist.
        """
        try:
            f = open(name)
            f.close()
        except:
            return False
        return True

    def showError(self, text, icon = QMessageBox.Warning):
        #Show error message
        errormsg = QMessageBox()
        errormsg.setIcon(icon)
        errormsg.setText(text)
        errormsg.exec_()
        return errormsg

    def closeEvent(self, event):
        #Stops the measurement and closes the program.
        if self.reallyQuitDialog(): #Confirmation screen
            self.stopMeasuring()
            super().closeEvent(event)
        else:
            event.ignore()

    def reallyQuitDialog(self):
        #This is the confirmation screen before closing
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        exitstring = "Are you sure you wish to exit? Any unsaved data is lost!"
        msg.setText(exitstring)
        msg.setWindowTitle("Really Quit?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        button = msg.exec_()
        if button == 16384: # yes == 16384
            return True
        if button == 4194304:  # cancel == 4194304
            return False
        else:
            raise ValueError("The exit dialog returned an unknown button!")
           
if __name__ == '__main__':
    #Check if there already exists an QApplication. If not create a new one.
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    window = AlphalasGUI()
    app.exec_()