from gpio import *
from time import *
from ioeclient import IoEClient

LIGHT = 0
MOTION_SENSOR = 1
DOOR = 2

MODES = {
    '0': 'Off',
    '1': 'On',
    '2': 'Auto'
}

MODE_CODE = {
    value: key for key, value in MODES.items()
}

currentMode = 'Auto'

MIN_HOUR = 20
MAX_HOUR = 8

SLEEP = 1

DURATION = 15

light = False
lightDuration = 0

# IOeClient
CONFIG = {
    "type": "Door Light",
    "states": [
            {
                "name": "Mode",
                "type": "options",
                "options": MODES,
                "controllable": True
            },
        {
                "name": "Current Hour",
                "type": "number",
                "controllable": False,
                "minValue": 0,
                "maxValue": 23
        },
        {
                "name": "Auto Start Hour",
                "type": "number",
                "controllable": True,
                "minValue": 12,
                "maxValue": 23
        },
        {
                "name": "Auto End Hour",
                "type": "number",
                "controllable": True,
                "minValue": 0,
                "maxValue": 11
        },
        {
                "name": "Auto Duration",
                "type": "number",
                "controllable": True,
                "minValue": 1,
                "maxValue": (MIN_HOUR - MAX_HOUR) * 3600
        },
    ]
}


def onIoEStateSet(stateName, value):
    global MIN_HOUR, MAX_HOUR, DURATION, currentMode, light, lightDuration

    if stateName == "Mode":
        if value in MODES.keys():
            currentMode = MODES[value]

            if currentMode != 'Auto':
                light = False
                lightDuration = 0

            if currentMode == 'Off':
                lightOff()
            elif currentMode == 'On':
                lightOn()
        else:
            print("Unknown option", value)
    elif stateName == "Auto Start Hour":
        MIN_HOUR = int(float(value))
    elif stateName == "Auto End Hour":
        MAX_HOUR = int(float(value))
    elif stateName == "Auto Duration":
        DURATION = int(float(value))
    else:
        print("Unknown state", stateName, value)


def IoEUpdateState():
    IoEClient.reportStates(
        [MODE_CODE[currentMode], getCurrentHour(), MIN_HOUR, MAX_HOUR, DURATION])


def IoESetup():
    IoEClient.setup(CONFIG)
    IoEClient.onStateSet(onIoEStateSet)
    IoEUpdateState()


def lightOff():
    customWrite(LIGHT, '0')


def lightOn():
    customWrite(LIGHT, '2')


def getCurrentHour():
    currentTime = localtime(time())

    currentHour = currentTime[3]

    return currentHour


def checkHourCondition():
    currentHour = getCurrentHour()

    return currentHour >= MIN_HOUR or currentHour <= MAX_HOUR


def getMotionSensorInfo():
    return int(digitalRead(MOTION_SENSOR))


def getDoorInfo():
    return int(customRead(DOOR)[0])


def lightAlgorithm():
    global light, lightDuration

    if light:
        lightDuration += SLEEP

    if checkHourCondition() and (getMotionSensorInfo() or getDoorInfo()):
        light = True

        lightDuration = 0
    elif light and lightDuration >= DURATION:
        light = False

        lightDuration = 0

    if light:
        lightOn()
    else:
        lightOff()


def init():
    lightOff()

    IoESetup()


def main():
    while True:
        if currentMode == 'Auto':
            lightAlgorithm()

        IoEUpdateState()

        sleep(SLEEP)


if __name__ == "__main__":
    init()

    main()
