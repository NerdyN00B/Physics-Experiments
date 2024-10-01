# -*- coding: utf-8 -*-
"""


@author: ommenhbvan 

NB
I could find no way to set the exposure mode of the webcam using the cv2 library. 
Currently the webcam has an auto-exposure mode enabled, to prevent the output from clipping
When wanting to compare intensities of different measurements this function should be disabled.
It might be possible to do this using a different library.
"""


from PyQt5.QtWidgets import QApplication, QMainWindow,QMessageBox,QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QImage, QPixmap
import numpy
np = numpy
import sys
import os
import pyqtgraph as pg
import subprocess
try:
    import cv2
except:
    subprocess.run(["pip","install","opencv-python"]) # this installs the libraries that aren't installed by default
    import cv2
pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'g')
pg.setConfigOptions(antialias=True)




class EN_Measure_In_Time(QMainWindow):


    def __init__(self):

        super().__init__()


        #Open ui file with same name as current file
        filename=os.path.basename(__file__)
        uifilename=filename[:-2]+"ui"
        uic.loadUi(uifilename, self)

        self.xresolution = 1280 # change as needed. 640 pixels allows 30 fps capturing, given sufficient lighting
        self.xdata = np.arange(self.xresolution) 
        self.data = []
        # containers for x and y of the column graph

        self.plotItemCols=self.plotWidgetCols.getPlotItem() # This plot contains the mean of the columns
        self.plotItemCols.plot(pen='r')
        self.plotItemCols.setLabels(bottom ='Pixel ', left= 'Signal', title= 'CCD Slice')
        self.curveCols = self.plotItemCols.plot(pen='r')
        #self.plotItemCols.disableAutoRange(axis = 1)
        self.cursor1 = pg.InfiniteLine(300,movable = True,pen = 'y')
        self.cursor2 = pg.InfiniteLine(400,movable = True)#,pen = 'g')
        self.plotWidgetCols.addItem(self.cursor1)
        self.plotWidgetCols.addItem(self.cursor2)
        
        self.pix = QPixmap() # contains the image to show. 
        self.pix.load("webcamFiller.png") # shows the default welcome image
        self.isMeasuring = 0 # this is a flag to check if we are measuring. Makes sure we do not try to disconnect the webcam if it is already disconnected

        #create timer for updating graph
        self.timer = pg.QtCore.QTimer()
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.updateGraph)
        
        #create timer for acquiring data. everytime the timer times-out it will acquire another frame through the updateData method
        self.rate = 9 # the webcam reports it can only achieve 9 fps in 1280x1024 mode. in 640x480 mode 30 fps is possible.
        self.Camtimer = pg.QtCore.QTimer()
        # self.Camtimer.setInterval(1000/self.rate)
        self.Camtimer.timeout.connect(self.updateData)
        
        self.connectUI()
        self.show()


    def connectUI(self):
        self.SelectPathButton.clicked.connect(self.selectPath)
        self.SaveButton.clicked.connect(self.saveData)
        self.StartButton.clicked.connect(self.initTask)
        self.StopButton.clicked.connect(self.stop_measuring)
        self.cursor1.sigPositionChanged.connect(self.updateCursor1)
        self.cursor2.sigPositionChanged.connect(self.updateCursor2)
        self.cursor1Pos.valueChanged.connect(self.updateCursor1alt)
        self.cursor2Pos.valueChanged.connect(self.updateCursor2alt)
        self.timer.start() # start updating graph

    def initTask(self):
        """Init Task will start the webcam Measurements."""
        self.vc = cv2.VideoCapture(0) # in case of multiple connected webcams, one needs to set the index ("0" in this case) to select the desired cam.
        self.vc.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) # this sets the webcam resolution to 1280x1024. 640x480 is also possible 
        self.Camtimer.start()
        self.isMeasuring = 1
    def updateGraph(self):
        """Updates the graph widgets"""
        self.webcamLabel.setPixmap(self.pix) # sets the picture to be displayed. 
        if np.shape(self.xdata) == np.shape(self.data):
            try:
                self.curveCols.setData(self.xdata,self.data) # sets the graph data
            except TypeError:
                pass
    def updateData(self):
        # Let's acquire a frame from the webcam
        self.rval,frame = self.vc.read()
        if not self.rval: # rval is True if the read was succesful
            self.stop_measuring()
            self.Show_Error(text = "Could not communicate with the webcam. Please make sure the webcam is connected, and is not used by another program.\nReconnect the webcam if this error persists. ")
            return 1
        self.image = QImage(frame,frame.shape[1],frame.shape[0],frame.shape[1]*3,QImage.Format_RGB888).rgbSwapped() # This converts the array to an image that can be used by Qt. the rgb values have to be swapped (bgr) 
        self.pix = QPixmap(self.image) # we convert the QImage to QPixmap, which is optimized to be easily shown on screen. I could find no way to directly create a pixmap from an array
        color = np.mean(frame,axis = 2)
        self.data =  np.mean(color,axis = 0)
        self.cursor1Sig.setText("{:.1f}".format((self.data[int(self.cursor1.value())-1])))
        self.cursor2Sig.setText("{:.1f}".format((self.data[int(self.cursor2.value())-1])))

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
        extension = ".csv"
        
        splitSaveName = saveName.split('.')
        if len(splitSaveName) > 1:
            extension = "." + splitSaveName[1] 
        
        saveName = splitSaveName[0]

        if self.does_file_exist(saveName + extension):

            i = 1

            while self.does_file_exist(saveName + "(" + str(i) + ")" + extension):

                i += 1

            saveName = saveName + "(" + str(i) + ")"
        dest = "{}".format(savePath) + "/{}".format(saveName)
        try:
            np.savetxt(dest + extension, dataArray, delimiter = ",",header = "column 0 is pixels, column 1 is signal") # saves graph data
            self.image.save(dest + ".png") # saves image
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
    def stop_measuring(self):

        """
        Stops the measurement, no new data points will be acquired
        """
        if self.isMeasuring:
            self.vc.release()
            self.Camtimer.stop()
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

    def Show_Error(self,icon = QMessageBox.Warning,text = "Warning! This text should be changed as it is the default error text!"):
        errormsg = QMessageBox()
        errormsg.setIcon(icon)
        errormsg.setText(text)
        errormsg.exec_()
        return errormsg


    def updateCursor1(self):
        # if the cursor changed, change the textvalue
        cursorpos = self.cursor1.value()
        textval = self.cursor1Pos.value()
        if cursorpos == textval:
            pass
        else:
            self.cursor1Pos.setValue(cursorpos)
    def updateCursor2(self):
        # if the cursor changed, change the textvalue
        cursorpos = self.cursor2.value()
        textval = self.cursor2Pos.value()
        if cursorpos == textval:
            pass
        else:
            self.cursor2Pos.setValue(cursorpos)
    def updateCursor1alt(self):
        cursorpos = self.cursor1.value()
        textval = self.cursor1Pos.value()
        if cursorpos == textval:
            pass
        else:
            #if the text changed first, move the cursor
            self.cursor1.setValue(textval)
    def updateCursor2alt(self):
        cursorpos = self.cursor2.value()
        textval = self.cursor2Pos.value()
        if cursorpos == textval:
            pass
        else:
            #if the text changed first, move the cursor
            self.cursor2.setValue(textval)
           
        #if 
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
