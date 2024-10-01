# -*- coding: utf-8 -*-
"""
Created on Fri Aug 31 11:58:53 2018

@author: kautz
@coauthor: ommenhbvan 2-sept-2018
"""


from PyQt5.QtWidgets import QApplication, QMainWindow,QMessageBox,QFileDialog
from PyQt5 import uic
import datetime
import time
import numpy

from utils import get_available_mydaq_devices

np = numpy
import sys
import os
import pyqtgraph as pg
import nidaqmx as dx
import math



pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)




class EN_Measure_In_Time(QMainWindow):


    def __init__(self):

        super().__init__()


        #Open ui file with same name as current file
        filename=os.path.basename(__file__)
        uifilename=filename[:-2]+"ui"
        uic.loadUi(uifilename, self)




        #ydata0 is the data corresponding to dmm0
        self.xdata = [] #Time array
        self.data = []

        #sampling rate
        self.rate=1000 # samples / s

        # number of decimals to save with
        self.decimals = 4 # 4 is maximum myDAQ accuracy
        #Sets up all plot information.
        self.plotItem0=self.plotWidget0.getPlotItem()
        self.plotItem0.plot(pen='k')

        self.manualLimits = False # Use autoscaling of y-axis by default.
        self.isMeasuring = 0

        self.plotItem0.setLabels(bottom ='Time (s)', left= 'Volt (V)', title= 'MyDAQ')

        self.chunkSize=50
        self.curve = self.plotItem0.plot(pen='k')

        
        #create timer to timeout a stuck myDAQ
        self.datatimer = pg.QtCore.QTimer()
        self.datatimer.setInterval(1000)
        self.datatimer.timeout.connect(self.myDAQtimeout)
        
        self.lastUpdateTime = float(time.time())
        print(self.lastUpdateTime)
        
        self.datatimer.start()
        
        self.timedOut = 0
        self.lastRead = 0
        self.reads = 0
        
        self.connectUI()
        self.show()

    def connectUI(self):
        self.SelectPathButton.clicked.connect(self.selectPath)
        self.SaveButton.clicked.connect(self.saveData)
        self.StartButton.clicked.connect(self.initTask)
        self.StopButton.clicked.connect(self.stop_measuring)
        self.ClearButton.clicked.connect(self.clearData)
        self.ManualLimits.clicked.connect(self.useManualLimits)
        #self.timer.start() # start updating graph

    def initTask(self):
        try:
            if not self.isMeasuring:
                self.task = dx.Task()
                try:
                    self.rate = float(self.RateEdit.text())
                    if self.rate > 100:
                        self.chunkSize = math.ceil(float(self.rate/20.))
                    else:
                        self.chunkSize = 1
                except ValueError:
                    pass
                self.RateEdit.setEnabled(False)

                available_devices = get_available_mydaq_devices()
                selected_device = available_devices[0] if available_devices else "myDAQ1"
                print(f"Attempting to use {selected_device}.")

                self.task.ai_channels.add_ai_voltage_chan(f"{selected_device}/ai0")
                self.task.timing.cfg_samp_clk_timing(self.rate,sample_mode=dx.constants.AcquisitionType.CONTINUOUS)
                self.task.register_every_n_samples_acquired_into_buffer_event(self.chunkSize, self.updateData)
                self.task.start()
                
                self.isMeasuring = 1
                self.reads = 0
                self.lastRead = -1
                
            else:
                print("we were already measuring!")
        except dx.DaqError as err:
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("No myDAQ could be found connected to the system. Try reconnecting your myDAQ")
            errormsg.exec_()
            print(err)
            
    def myDAQtimeout(self):        
        if self.reads > self.lastRead:
            self.lastRead = self.reads
        elif self.isMeasuring:
            self.timedOut += 1
            if self.timedOut == 1 and self.isMeasuring:
                errormsg = QMessageBox()
                errormsg.setIcon(QMessageBox.Warning)
                errormsg.setText("No data received from the myDAQ for 2 seconds. Either the device has been disconnected or too much power was drawn from the power rails (most likely caused by a short circuit). Please save your current data and exit the program using the (X) in the top right.")
                errormsg.exec_()
            else:
                pass
    def updateGraph(self):
        ### Currently time is set by counting the number of read samples,
        # setting the the first sample to be t=0, and then inferring the times of the next samples
        # from the samplerate and the number a sample has (how many samples have come before).
        # This works because data is written into the buffer continuously and data is read by us
        # from the buffer in order of which the data was measured.

        secondsBack = self.ShowLast.value()
        
        #Only 100.000 points can be shown at once. Change the value of seconds back if it is set too high.
        if secondsBack * self.rate > 100000:
            secondsBack = 100000 / self.rate
            self.ShowLast.setValue(secondsBack)
        
        if self.ManualLimits.isChecked():
            try:
                self.Vmin = float(self.VminEdit.text())
                self.Vmax = float(self.VmaxEdit.text())
            except ValueError:
                pass
            self.plotWidget0.setRange(yRange=[self.Vmin,self.Vmax])
        
        viewSampleSize = int(secondsBack * self.rate) # array slices must be integers
        
        if len(self.xdata) == len(self.data):
            self.curve.setData(self.xdata[-viewSampleSize:], self.data[-viewSampleSize:])

    def useManualLimits(self):
        if self.ManualLimits.isChecked():
            self.manualLimits = True
            self.VmaxEdit.setEnabled(True)
            self.VminEdit.setEnabled(True)
            self.plotItem0.disableAutoRange(axis = 1)
        else:
            self.manualLimits = False
            self.VmaxEdit.setEnabled(False)
            self.VminEdit.setEnabled(False)
            self.plotItem0.enableAutoRange(axis = 1)
            
    def clearData(self):
        self.xdata, self.data = [], []
        self.updateGraph()

    def updateData(self,task_handle, every_n_samples_event_type, number_of_samples, callback_data):
        # How many samples have we read?
        numberOfSamples = self.reads*self.chunkSize
        
        # Read the new batch
        newdata = self.task.read(number_of_samples_per_channel=self.chunkSize)
        self.reads += 1
        
        # Create the time-coordinates for the new data
        timeFirstSample = numberOfSamples/self.rate
        timeLastSample = timeFirstSample + self.chunkSize/self.rate
        timedata = np.linspace(timeFirstSample,timeLastSample, self.chunkSize, endpoint=False)
        
        self.data.extend(newdata)
        self.xdata.extend(timedata)
        
        currentTime = float(time.time())
        
        if currentTime > self.lastUpdateTime + 0.02:
            self.updateGraph()
            self.lastUpdateTime = currentTime
        
        return 0
    
    def selectPath(self):
        self.SaveDirectoryText.setText(QFileDialog.getExistingDirectory())

    def saveData(self):
        """
        Saves the current data and time arrays to a file
        """
        # I transpose the array to have each row be a new sample. I think
        # this makes more sense.
        dataArray = np.array([self.xdata,self.data]).transpose()

        savePath = self.SaveDirectoryText.toPlainText()
        saveName = self.FileName.toPlainText()
        
        if savePath[1:] == ':/':
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("You seem to be trying to save directly to a disk. E.g. you might be trying to save directly to the P:/ disk. Our fileservers do not support this, and we recommend you to save data to a folder on your P-disk regardless. Please try to save to a P-disk folder.")
            errormsg.exec_()
            return False

        saveNameSplit = os.path.splitext(os.path.basename(saveName))
        saveName = saveNameSplit[0]
        extension = '.csv'
        if len(saveNameSplit) > 1:
            lastExtension = saveNameSplit[len(saveNameSplit)-1]
            try:
                if lastExtension[0] == '.':
                    extension = lastExtension 
                    print("Extension detected:", extension)
            except IndexError:
                pass
            saveName = saveName + extension
        
        
        
        if self.does_file_exist(saveName):

            i = 1

            while self.does_file_exist(saveName + "(" + str(i) + ")"):

                i += 1

            saveName = saveName + "(" + str(i) + ")"
                
                
        dest = os.path.join(savePath, saveName)
        try:
            np.savetxt(dest,dataArray,"%.{}f".format(self.decimals),delimiter = ",",header = "axis 0 is time, axis 1 is Voltage")
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
        except ValueError:
            errormsg = QMessageBox()
            errormsg.setIcon(QMessageBox.Warning)
            errormsg.setText("Python has raised a ValueError. This is probably due to the fact that you're trying to write directly to a disk. Write to a folder instead. This bug should have been fixed--please also contact a TA.")
            errormsg.exec_()
        # Catch a save error.
    def stop_measuring(self):

        """
        Stops the measurement, no new data points will be acquired
        """
        if self.isMeasuring:
            self.task.stop()
            self.task.close()
            self.isMeasuring = 0
            self.RateEdit.setEnabled(True)
        else:
            print("we were already stopped!")
    def closeEvent(self, event):

        """
        First checks if the user is sure the program should be terminated.
        Stops the measurement and closes the program correctly.
        """
        if self.reallyQuitDialog():
            self.stop_measuring()
            super().closeEvent(event)
        else:
            event.ignore()
    def reallyQuitDialog(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        exitstring = "Are you sure you wish to exit? Any unsaved data is lost!"
        msg.setText(exitstring)
        msg.setWindowTitle("Really Quit?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        button = msg.exec_()
        if button == 16384:
            return True
        if button == 4194304:
            return False
        else:
            raise ValueError("The exit dialog returned an unknown button!")
        # yes == 16384
        # cancel == 4194304
        # They are some convenient hex values

    def does_file_exist(self, name):

        """
        Checks if there already exists a file named name in the current
        directory.

        - name is a string with the name of the file, e.g. "Foo.txt".
        - Returns True if it already does exist.
        """

        try:
            f = open(name)
            f.close()

        except:
            return False

        return True


# This file can be run on its own, or it can be used by another file to import classes from.
# Here wether the program is run on its own. If so, the application is started
if __name__ == '__main__':



    # here we check if there already exists an QApplication. If not we create a new one.
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    #check which dmm was selected



    # here we create an instance of the EN_Resistances_Window class defined above
    window = EN_Measure_In_Time()

    # here the application is started

    app.exec_() #for use an in interactive shell
    #sys.exit(app.exec_()) #for use from terminal
