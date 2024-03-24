from gpio import *
from time import *
from ioeclient import IoEClient

COFFEE_PIN = 0
LIGHT_PIN = 1
HEATING_PIN = 2
TEMPERATURE_PIN = A0

SLEEP = 1

T_MIN = 21

MORNING_HOUR = 7

LIGHT_MODES = ['off', 'dim', 'on']
LIGHT_TIMEOUT = 10

isHeating = False
heatedAlready = False

lightMode = LIGHT_MODES[0]
lightModeTime = 0

coffeeOn = False

ON_OFF_MODE_OPTIONS = {
    '0': 'Off',
    '1': 'On',
    '2': 'Auto'
}

ON_OFF_MODE_CODE = {
    value: key for key, value in ON_OFF_MODE_OPTIONS.items()
}

LIGHT_MODE_OPTIONS = {
    '0': 'Off',
    '1': 'Dim',
    '2': 'On',
    '3': 'Auto'
}

LIGHT_MODE_CODE = {
    value: key for key, value in LIGHT_MODE_OPTIONS.items()
}

heatingModeOption = 'Auto'
coffeeModeOption = 'Auto'
lightModeOption = 'Auto'

# IOeClient
CONFIG = {
    "type": "Morning Routine",
    "states": [
            {
                "name": "Morning Hour",
                "type": "number",
                "controllable": True,
                "minValue": 0,
                "maxValue": 23
            },
        {
                "name": "Current Hour",
                "type": "number",
                "minValue": 0,
                "maxValue": 23
            },
        {
                "name": "Heating Mode",
                "type": "options",
                "options": ON_OFF_MODE_OPTIONS,
                "controllable": True
            },
        {
                "name": "Current Temperature",
                "type": "number",
                "unit": "&deg;C",
                "imperialUnit": "&deg;F",
                "toImperialConversion": "x*1.8+32",
                "toMetricConversion": "(x-32)/1.8",
                "decimalDigits": 1
            },
        {
                "name": "Auto Heat Temperature",
                "type": "number",
                "unit": "&deg;C",
                "imperialUnit": "&deg;F",
                "toImperialConversion": "x*1.8+32",
                "toMetricConversion": "(x-32)/1.8",
                "decimalDigits": 1,
                "controllable": True,
                "minValue": -100,
                "maxValue": 35
            },
        {
                "name": "Coffee Machine Mode",
                "type": "options",
                "options": ON_OFF_MODE_OPTIONS,
                "controllable": True
            },
        {
                "name": "Light Mode",
                "type": "options",
                "options": LIGHT_MODE_OPTIONS,
                "controllable": True
            },
    ]
}


def onIoEStateSet(stateName, value):
    global T_MIN, MORNING_HOUR, isHeating, heatedAlready, lightMode, lightModeTime, coffeeOn, heatingModeOption, coffeeModeOption, lightModeOption

    if stateName == 'Morning Hour':
        MORNING_HOUR = int(float(value))
    elif stateName == "Heating Mode":
        if value in ON_OFF_MODE_OPTIONS.keys():
            heatingModeOption = ON_OFF_MODE_OPTIONS[value]

            if heatingModeOption == 'Off':
                turnOffHeating()
            elif heatingModeOption == 'On':
                turnOnHeating()

            if heatingModeOption != 'Auto':
                isHeating = False

                heatedAlready = False
        else:
            print("Unknown option", value)
    elif stateName == "Auto Heat Temperature":
        T_MIN = float(value)
    elif stateName == "Coffee Machine Mode":
        if value in ON_OFF_MODE_OPTIONS.keys():
            coffeeModeOption = ON_OFF_MODE_OPTIONS[value]

            if coffeeModeOption == 'Off':
                coffeeMachineOff()
            elif coffeeModeOption == 'On':
                coffeeMachineOn()

            if coffeeModeOption != 'Auto':
                coffeeOn = False
        else:
            print("Unknown option", value)
    elif stateName == "Light Mode":
        if value in LIGHT_MODE_OPTIONS.keys():
            lightModeOption = LIGHT_MODE_OPTIONS[value]

            if lightModeOption == 'Off':
                lightOff()
            elif lightModeOption == 'Dim':
                lightDim()
            elif lightModeOption == 'On':
                lightOn()

            if lightModeOption != 'Auto':
                lightMode = LIGHT_MODES[0]

                lightModeTime = 0
        else:
            print("Unknown option", value)
    else:
        print("Unknown state", stateName, value)


def IoEUpdateState():
    IoEClient.reportStates([MORNING_HOUR, getCurrentTimeInfo()[
                           0], ON_OFF_MODE_CODE[heatingModeOption], getTemperature(), T_MIN, ON_OFF_MODE_CODE[coffeeModeOption], LIGHT_MODE_CODE[lightModeOption]])


def IoESetup():
    IoEClient.setup(CONFIG)
    IoEClient.onStateSet(onIoEStateSet)
    IoEUpdateState()


def getCurrentTimeInfo():
    currentTime = localtime(time())

    currentHour = currentTime[3]

    currentMinute = currentTime[4]

    return currentHour, currentMinute


def checkTimeCondition():
    currentHour, currentMinute = getCurrentTimeInfo()

    return (currentHour - MORNING_HOUR) == 0 and currentMinute == 0


def lightOff():
    customWrite(LIGHT_PIN, '0')

    print('Light off')


def lightDim():
    customWrite(LIGHT_PIN, '1')

    print('Light dim')


def lightOn():
    customWrite(LIGHT_PIN, '2')

    print('Light on')


def lightControl():
    global lightMode
    global lightModeTime

    currentIndex = LIGHT_MODES.index(lightMode)

    if not currentIndex or (currentIndex and lightModeTime >= LIGHT_TIMEOUT):
        nextIndex = min(currentIndex + 1, len(LIGHT_MODES) - 1)

        lightMode = LIGHT_MODES[nextIndex]

        if currentIndex != nextIndex:
            [lightOff, lightDim, lightOn][nextIndex]()

            lightModeTime = 0

    lightModeTime += SLEEP


def temperatureToCelsius(t):
    return float(t)*200/(HIGH-LOW)-100


def getTemperature():
    t = analogRead(TEMPERATURE_PIN)

    return temperatureToCelsius(t)


def turnOnHeating():
    global isHeating

    digitalWrite(HEATING_PIN, HIGH)

    isHeating = True

    print('Heating on')


def turnOffHeating():
    global isHeating, heatedAlready

    digitalWrite(HEATING_PIN, LOW)

    isHeating = False

    heatedAlready = True

    print('Heating off')


def heatingControl(t):
    global isHeating
    global heatedAlready

    if t < T_MIN and not isHeating and not heatedAlready:
        turnOnHeating()

    elif t > T_MIN and isHeating:
        turnOffHeating()


def climateControl():
    t = getTemperature()

    heatingControl(t)


def coffeeMachineOff():
    customWrite(COFFEE_PIN, '0')

    print('Coffee off')


def coffeeMachineOn():
    customWrite(COFFEE_PIN, '1')

    print('Coffee on')


def coffeeControl():
    global coffeeOn

    if not coffeeOn:
        coffeeMachineOn()

        coffeeOn = True


def resetData():
    global isHeating, heatedAlready, lightMode, coffeeOn, lightModeTime

    isHeating = False

    heatedAlready = False

    lightMode = LIGHT_MODES[0]

    coffeeOn = False

    lightModeTime = 0


def init():
    resetData()

    turnOffHeating()

    lightOff()

    coffeeMachineOff()

    IoESetup()


def taskAlgorithm():
    global heatedAlready, lightMode

    if checkTimeCondition():
        if heatingModeOption == 'Auto':
            climateControl()

        if lightModeOption == 'Auto':
            lightControl()

        if coffeeModeOption == 'Auto':
            coffeeControl()

    # still morning, time condition is already false, but room wasn't heated yet
    # or light cicle is not finished
    elif LIGHT_MODES.index(lightMode) > 0 or isHeating:
        if heatingModeOption == 'Auto' and not heatedAlready:
            climateControl()

        if lightModeOption == 'Auto' and LIGHT_MODES.index(lightMode) < len(LIGHT_MODES):
            lightControl()
    else:
        resetData()

    IoEUpdateState()

    sleep(SLEEP)


def main():
    while True:
        taskAlgorithm()


if __name__ == "__main__":
    init()

    main()
