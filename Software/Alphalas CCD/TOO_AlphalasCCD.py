"""
AlphalasCCD.py
Developed by Koen j.M. Schouten

ALPHALAS CCD
	v1.0

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

	This code demonstrates how to use the CCD-2000-D(-UV) or CCD-S3600-D(-UV) device. Also, at the end
    an example code is given. This example will initialize & configure the device with the user-specified parameters, then it 
    will acquire and fetch the data and return them as a numpy array.

	PYTHON INSTRUCTIONS:
	The code works with Python version 3.7 or higher. Earlier versions may also work, but have not been tested.
    This code requires the numpy library and the fts2xx library. Do not hesitate to contact us at TOO@physics.leidenuniv.nl if anything is unclear.
"""
import numpy as np
import ftd2xx as ftd

class DeviceSettings():
    #This class contains the settings, properties and the commands to communicate with the various
    #ALPHALAS devices.
    def __init__(self):
        #Names for the compatible devices for this programm
        self.possibleDevices = ['ALPHALAS CCD-2000-D(-UV)' ,'CCD-S3600-D(-UV) B']

        self.settings = {
            "integration_time" : 5000, # integration time in us
            "timeout_time" : 500, # timeout times in ms
            "shots_per_acquisition" : 1, # number of shots (frames) per acquisition
            "trigger" : 0, # trigout offset before integration (0 = off, 1 = on)
            "dark_correction" : 0, # hardware dark correction (0 = off, 1 = on)
            self.possibleDevices[0] : {
                "array_size" : 2048, # Array size for CCD-2000-D
                "min_integration_time" : 5000, # minimal integration time for CCD-2000-D
                "min_shots_per_acquisition" : 1, # minimum shots per acquisition
                "min_trigger" : 0, # minimum value for trigger
                "min_dark_correction" : 0, # minimum value for dark correction
            },
            self.possibleDevices[1] : {
                "array_size" : 3648, # Array size for CCD-S3600-D
                "min_integration_time" : 10, # minimal integration time for CCD-2000-D
                "min_shots_per_acquisition" : 1, # minimum shots per acquisition
                "min_trigger" : 0, # minimum value for trigger
                "min_dark_correction" : 0, # minimum value for dark correction
            }
        }

    def updateSetting(self, setting, value, ccdString):
        #Update a setting to the given value. For this, specify the CCD which is in use.
        #returns true iff updated. Also makes sure that the value is above the minimum value.
        value = max(value, self.settings[ccdString]['min_' + setting])
        if self.settings[setting] != value:
            self.settings[setting] = value
            return True
        
        return False

    def commands(self):
        #Return a dictionary with all the byte constants which specify a certain command
        #with the specified settings. Some actions contain an array with more than 1 command,
        #which should be executed subsequently. All actions have both a write and
        #read command, which should be executed subsequently.
        return {
            self.possibleDevices[0] : { # Commands for the CCD-2000-D
                "initialize" : { # Commands for setting the data format to binary
                    'writeCommands' : [b'F0\r'], 
                    'readCommands' : [3]
                },
                "set_integration_time" : { # Commands for setting the integration time (in ms)
                    'writeCommands' :  [str.encode("I{0}\r".format(int(self.settings["integration_time"] / 1000)))], 
                    'readCommands' : [4]
                },
                "set_shots_per_acquisition" : {  #Commands for setting the amount of shots per acquisition
                    'writeCommands' : [str.encode("R{0}\r".format(self.settings["shots_per_acquisition"]))], 
                    'readCommands' : [4]
                },
                "set_trigger" : { # Set the trigger mode of the alphalas to software trigger
                    'writeCommands' : [b'E1\r'], 
                    'readCommands' : [3]
                },
                "start_acquisition" : { # Commands for starting the acquisition
                    'writeCommands' : [b'S\r'], 
                    'readCommands' : []
                },
                "wait_for_data_fetch" : { # Wait until the CCD is ready
                    "function" : "read",
                    "value" : b'DONE\r'
                }, 
                "fetch_readout" : { # Ask the CCD to fetch the data
                    'writeCommands' : [b'G\r'], 
                    'readCommands' : [4096]
                }
            },
            self.possibleDevices[1] : { # Commands for the CCD-S3600-D
                "set_integration_time" : { # Command for setting the integration time (in us)
                    'writeCommands' : [b'\xc1', self.settings['integration_time'].to_bytes(4, 'big')], 
                    'readCommands' : [1]
                },
                "set_shots_per_acquisition" : { # Command for setting the amount of shots per acquisition
                    'writeCommands' : [b'\xc2', self.settings["shots_per_acquisition"].to_bytes(4, 'big')], 
                    'readCommands' : [1]
                },
                "set_trigger" : { # Set the trigger mode of the alphalas to software trigger
                    'writeCommands' : [b'\xc3', self.settings["trigger"].to_bytes(1, 'big')], 
                    'readCommands' : [1]
                },
                "set_dark_correction" : { # Turn on/off the dark correction
                    'writeCommands' : [b'\xc5', self.settings["dark_correction"].to_bytes(1, 'big')], 
                    'readCommands' : [1]
                },
                "start_acquisition" : { # Command for starting the acquisition
                    'writeCommands' : [b'\xc6'], 
                    'readCommands' : []
                },
                "wait_for_data_fetch" : { # Wait until the CCD is ready
                    "function" : 'getQueueStatus',
                    'value' : 7296
                },
                "fetch_readout" : { # Ask the CCD to fetch the data
                    'writeCommands' : [], 
                    'readCommands' : [7296]
                }
            }
        }

class AlphalasCCD():
    #This class contains all the functions regarding communication with the Alphalas CCD

    def __init__(self):
        self.deviceSettings = DeviceSettings()
        self.initializeCCD()

    def initializeCCD(self):
        #This method will look for connected Alphalas CCD devices. 
        devices = ftd.listDevices(2)
        self.ccdString = 0

        if not devices:
            self.device = 0
            return 0
        
        #Search for the compatible devices
        for i in range(len(devices)):
            if devices[i].decode('utf-8') in self.deviceSettings.possibleDevices:
                self.ccdString = devices[i].decode('utf-8')
                self.device = ftd.open(i)
                self.device.setTimeouts(self.deviceSettings.settings['timeout_time'], self.deviceSettings.settings['timeout_time'])
        
        if not self.ccdString:
            self.device = 0
            return 0

        #Print the details of the CCD
        print("Connected to device: \n" + str(ftd.getDeviceInfoDetail()))
        
        #Execute the commands to setup the CCD
        self.executeCommand("initialize")
        self.executeCommand("set_integration_time")
        self.executeCommand("set_shots_per_acq")
        self.executeCommand("set_trigger")
        self.executeCommand("set_dark_correction")

        self.preparedShots = 0
    
    def getArraySize(self):
        #Get the array size of the CCD
        return self.deviceSettings.settings[self.ccdString]['array_size']

    def executeCommand(self, command):
        #Execute a given command
        response = []

        #Check if command exists
        if command in self.deviceSettings.commands()[self.ccdString]:
            writeCommands = self.deviceSettings.commands()[self.ccdString][command]['writeCommands']
            readCommands = self.deviceSettings.commands()[self.ccdString][command]['readCommands']

            #Execute the write commands
            for writeCommand in writeCommands:
                self.device.write(writeCommand)

            #Execute the read commands
            for readCommand in readCommands:
                response.append(self.device.read(readCommand))

        return response

    def updateSetting(self, setting, value):
        #Update a setting to the given value
        if self.deviceSettings.updateSetting(setting, value, self.ccdString):
            if "set_" + setting in self.deviceSettings.commands()[self.ccdString]:
                self.executeCommand("set_" + setting)

    def readoutData(self):
        #read out the data from the Alphalas CCD

        #Prepare the CCD for the data acquisition
        self.prepareForAcquisition()

        #Prepare the arry which will store all the data
        alldata = np.zeros((self.deviceSettings.settings['shots_per_acquisition'], self.deviceSettings.settings[self.ccdString]['array_size']))
       
        #Loop through the shots per acq
        for i in range(self.deviceSettings.settings["shots_per_acquisition"]):
            #Fetch a single readout
            alldata[i] = self.fetchSingleReadout()

        return np.mean(alldata, axis = 0) #Returns mean of data

    def prepareForAcquisition(self):
        #Prepares the CCD for acquisition
        self.executeCommand("start_acquisition")

        #Wait until the CCD is ready if necessary
        if self.deviceSettings.commands()[self.ccdString]['wait_for_data_fetch']['function'] == 'read':
            response = ''
            while response != self.deviceSettings.commands()[self.ccdString]['wait_for_data_fetch']['value']:
                response = self.device.read(5)

        #Set the amount of shots prepared to the shots per acquisition
        self.preparedShots = self.deviceSettings.settings['shots_per_acquisition']

    def fetchSingleReadout(self):
        #Fetch a sigle readout (Note that the CCD has to be prepared for
        #data acquisition before this function can be called).
        if self.preparedShots == 0:
            return False

        #Wait until the CCD is ready if necessary
        if self.deviceSettings.commands()[self.ccdString]['wait_for_data_fetch']['function'] == 'getQueueStatus':
            queuesize = 0
            while queuesize < self.deviceSettings.commands()[self.ccdString]['wait_for_data_fetch']['value']:
                queuesize = self.device.getQueueStatus()
        
        #Get the response of the CCD
        response = self.executeCommand("fetch_readout")[0]
        self.preparedShots -= 1

        return np.frombuffer(response, dtype= '>u2')
    
    def capture(self, inttime):
        #Fetches a single shot from the CCD with integration time in us
        alphalasCCD.updateSetting("integration_time", inttime) #Update integration time
        alphalasCCD.updateSetting("shots_per_acquisition", 1) #Set to one shot

        return self.readOutData()

    def exitWithError(self, error=''):
        #Close the device if an error occured
        print(error)
        self.closeDevice()

    def closeDevice(self):
        #Close the device
        if self.device:
            self.device.close()

#Here some example code for retrieving data from the Alphalas
if __name__ == '__main__':
    #Connect to CCD and change settings
    alphalasCCD = AlphalasCCD()
    alphalasCCD.updateSetting("integration_time", 5000)
    alphalasCCD.updateSetting("shots_per_acquisition", 1)

    #Retreive the data
    data = alphalasCCD.readoutData()
    print(data)