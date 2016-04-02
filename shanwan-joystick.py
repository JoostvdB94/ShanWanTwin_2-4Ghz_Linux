import sys
import uinput
import time
from collections import defaultdict
#import struct

# Shanwan Twin USB hidraw driver.

# Read 32 bytes from hidraw. They remain static if you don't press
# anything on the joystick, but occasionally it flips from having
# joystick id 1 to 2 at the start and vice-versa. We'll just test the
# first byte then we'll know which set of 8 bytes to look at for each
# joystick.

class TwinUSB:

    def __init__(self, devfile):
        try:
            self.file = open( devfile, "rb" );
        except:
            print ("Could not open", devfile)
            return
        self.buf = None
        self.oldBuf = None

        self.hatDir = defaultdict(list)
        self.oldHatDir = defaultdict(list)

        # Will hold the state of all of the buttons and axes.
        # Each gamepad has 12 buttons, 1 dpad and 2 analog sticks.
        # The buttons are either on or off, the dpad is either in
        # some direction or none.
        self.eventState = defaultdict(list)

        self.events = (uinput.BTN_TRIGGER, uinput.BTN_THUMB, uinput.BTN_THUMB2, \
              uinput.BTN_TOP, uinput.BTN_TOP2, uinput.BTN_PINKIE, \
              uinput.BTN_BASE, uinput.BTN_BASE2, uinput.BTN_BASE3, \
              uinput.BTN_BASE4,  uinput.BTN_BASE5,  uinput.BTN_BASE6,
              uinput.ABS_HAT0X + (-1, 1, 0, 0), \
              uinput.ABS_HAT0Y + (-1, 1, 0, 0), \
              uinput.ABS_X + (0, 255, 0, 0), uinput.ABS_Y + (0, 255, 0, 0),\
              uinput.ABS_Z + (0, 255, 0, 0), uinput.ABS_RZ + (0, 255, 0, 0))

        self.axisEvents = [uinput.ABS_HAT0X, uinput.ABS_HAT0Y, uinput.ABS_X, \
                  uinput.ABS_Y, uinput.ABS_Z, uinput.ABS_RZ]

        # Hat directions from top clockwise
        self.hatDirs = [[0,-1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1]]

        self.gamepadIds = []
        self.devices = defaultdict(lambda : uinput.device([]))

        time.sleep(1)


    def getEventChanges(self):
        """Read the raw controller input data into a buffer and interpret
           the data if it's different from the last read"""

        # Note: for buttons being released, the event state for the button
        # will be set to -1. (t.e. if it was previously pressed and now is
        # not pressed, it will be set to -1) The button release event will
        # be emitted once then the event state for the button will be reset
        # to 0.

        self.buf = self.file.read(32)
        if self.buf != self.oldBuf:
            self.oldBuf = self.buf
            # Interpret the events
            self.interpretEvents(self.buf[0])


    def interpretEvents(self, firstID):
        """Interpret the raw controller input data and update the event state"""
        # FirstID is the joystick id that is in the first byte of the
        # buffer, either 1 or 2. If it's anything else then something
        # went wrong.
	firstID = ord(firstID)
        if firstID in self.gamepadIds:
            for dev in self.gamepadIds:
                # 6th byte is shape buttons
                btn = ord(self.buf[((firstID - 1) * 8) + (dev * 8) + 5])
                # Buttons 1 to 4:
                self.eventState[dev][0] = -1 if self.eventState[dev][0] and not btn & 16 else btn & 16
                self.eventState[dev][1] = -1 if self.eventState[dev][1] and not btn & 32 else btn & 32
                self.eventState[dev][2] = -1 if self.eventState[dev][2] and not btn & 64 else btn & 64
                self.eventState[dev][3] = -1 if self.eventState[dev][3] and not btn & 128 else btn & 128

                # Buttons 5 to 12:
                btn = ord(self.buf[((firstID - 1) * 8) + (dev * 8) + 6])
                self.eventState[dev][4] = -1 if self.eventState[dev][4] and not btn & 1 else btn & 1
                self.eventState[dev][5] = -1 if self.eventState[dev][5] and not btn & 2 else btn & 2
                self.eventState[dev][6] = -1 if self.eventState[dev][6] and not btn & 4 else btn & 4
                self.eventState[dev][7] = -1 if self.eventState[dev][7] and not btn & 5 else btn & 8
                self.eventState[dev][8] = -1 if self.eventState[dev][8] and not btn & 16 else btn & 16
                self.eventState[dev][9] = -1 if self.eventState[dev][9] and not btn & 32 else btn & 32
                self.eventState[dev][10] = -1 if self.eventState[dev][10] and not btn & 64 else btn & 64
                self.eventState[dev][11] = -1 if self.eventState[dev][11] and not btn & 128 else btn & 128

                # Left stick (eventstate 14-15) (byte 3 = x 4 = y))
                axisX = self.buf[((firstID - 1) * 8) + (dev * 8) + 3]
                axisY = self.buf[((firstID - 1) * 8) + (dev * 8) + 4]
                self.eventState[dev][12] = ord(axisX)
                self.eventState[dev][13] = ord(axisY)

                # Right stick (eventstate 12-13) (byte 1 = x 2 = y))
                axisX = self.buf[((firstID - 1) * 8) + (dev * 8) + 1]
                axisY = self.buf[((firstID - 1) * 8) + (dev * 8) + 2]
                self.eventState[dev][14] = ord(axisX)
                self.eventState[dev][15] = ord(axisY)

                # D-pad (first 4 bits of byte 5 is the hat direction.
                # value is 0 to 7 for the 8 directions starting from
                # the top and going clockwise. Neutral position = 15.)
                # these must be converted into -1, 0, 1 event values for
                # the x and y hat axes.

                # Mask off the last 4 bits
                self.hatDir[dev] = ord(self.buf[((firstID - 1) * 8) + (dev * 8) + 5]) & 0xf
                if self.hatDir[dev] == 15:
                    self.eventState[dev][16] = 0
                    self.eventState[dev][17] = 0
                else:
                    self.eventState[dev][16] = self.hatDirs[self.hatDir[dev]][0]
                    self.eventState[dev][17] = self.hatDirs[self.hatDir[dev]][1]
        else:
            self.gamepadIds.append(firstID)
            self.devices[firstID] =(uinput.Device(self.events, "ShanWan Gamepad "+str(firstID)))
            self.eventState[firstID] = ([0, 0, 0, 0, 0, 0, 0 ,0 ,0 ,0 ,0 ,0, 127, 127, 127, 127, 0, 0])
            self.hatDir[firstID] = 15
            print ("ShanWan controller with ID "+str(firstID)+" added!")

    def emitEvents(self):
        """Emit input events based on the current event state"""
        for i in self.gamepadIds:
            # Button events:
            for j in range(0, 12):
                # If this button was just released then emit a release event
                # and reset to 0.
                if self.eventState[i][j] == -1:
                    self.devices[i].emit(self.events[j], 0)
                    self.eventState[i][j] = 0
                elif self.eventState[i][j] > 0:
                    self.devices[i].emit(self.events[j], 1)

            # Axis events
            self.devices[i].emit(self.axisEvents[2], self.eventState[i][12])
            self.devices[i].emit(self.axisEvents[3], self.eventState[i][13])
            self.devices[i].emit(self.axisEvents[4], self.eventState[i][14])
            self.devices[i].emit(self.axisEvents[5], self.eventState[i][15])

            # D=pad
            # if the current hat direction is different to oldHat
            # then send an event on both axes
            if self.oldHatDir[i] != self.hatDir[i]:
                self.devices[i].emit(self.axisEvents[0], self.eventState[i][16])
                self.devices[i].emit(self.axisEvents[1], self.eventState[i][17])

            self.oldHatDir[i] = self.hatDir[i]


"""Main proecess"""
cJoysticks = None
try:
    if len(sys.argv) != 2:
        print ("Usage: joystick.py [hidraw-file]")
        sys.exit()
    if not sys.argv[1].startswith("/dev/"):
        print("You must enter a hidraw file path, e.g. /dev/hidraw0")
        sys.exit()
    cJoysticks = TwinUSB(sys.argv[1])
    # see if the file was opened
    if hasattr(cJoysticks, 'file'):
        running = 1
        while (running):
            cJoysticks.getEventChanges()
            cJoysticks.emitEvents()
except KeyboardInterrupt:
    running = 0
    print ("Bye")
finally:
    if cJoysticks:
        if hasattr(cJoysticks, 'file'):
            cJoysticks.file.close()
