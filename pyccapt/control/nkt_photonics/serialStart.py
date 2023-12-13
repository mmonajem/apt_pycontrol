from time import sleep

import serial

# Example Program using the control object
# Version 1.1

# Author Ian Baker

# Customise your comport to your Origami address
comPort = "COM9"

# Open the port
ser = serial.Serial(
	port=comPort,
	baudrate=38400,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS,
	rtscts=False
)
cmd = "ly_oxp2_dev_status"

ser.write(cmd.encode())
sleep(0.1)
dataStore = []
while ser.in_waiting:
	dataBack = ser.readline()
	dataStore.append(dataBack.decode())
ser.close()
sleep(1)
print(dataStore.decode())

# Set the laser into standby mode
# databack =origamiClassCLI.origClass.Standby(comPort)
# print(databack)


# Wait for it to warm up
# Either at initial turn on, or after a being in "Listen" mode 
# The laser will need to warm itself up to get ready
# Once its ready it returns status =33, here I just use the whole string 
# flag=0
# while (flag==0):
#     databack = origamiClassCLI.origClass.StatusRead(comPort)
#     print(databack)
#     if (databack=="ly_oxp2_dev_status 33\n"):
#         flag=1
#         print('Warmed up')
#
#
# ## Enable the output
# databack = origamiClassCLI.origClass.Enable(comPort)  ## Enable the laser output (to start with output is 0uJ)
# print(databack)
#
#
# ## Set the power out
# # Make sure power meter is in front of the output
# databack = origamiClassCLI.origClass.Power(comPort,25000)  ## This sets the laser to an output power
# print(databack)
# sleep(10)   # wait 10s
#
#
# ## turn the Emission off
# databack =origamiClassCLI.origClass.Standby(comPort)  ## By invoking standy it turns the emission off
# print(databack)
#
#
# ## set it to listen mode
# databack =origamiClassCLI.origClass.Listen(comPort)  ## Listen mode, so the laser just idles
# print(databack)
#
