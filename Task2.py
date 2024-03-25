from gpio import *
from time import *
from realhttp import RealHTTPClient
from ioeclient import IoEClient


TIMEOUT = 1

HAETING_PIN = 0
COOLING_PIN = 1
DISPLAY_PIN = 2
TEMPERATURE_PIN = A0

tMax = 32.0
tMin = 18.0
Mode = "Auto"

MODES = {
    "0": "Off",
    "1": "Cooling",
    "2": "Heating",
    "3": "Auto"
}
MODE_CODE = {
    value: key for key, value in MODES.items()
}

isHeating = False
isCooling = False

BATCH_LEN = 10
temperatures_batch = []


# IOeClient
CONFIG = {
    "type": "Thermostat",
    "states": [
        {
            "name": "Mode",
            "type": "options",
            "options": MODES,
            "controllable": True
        },
        {
            "name": "Temperature",
            "type": "number",
            "unit": "&deg;C",
            "imperialUnit": "&deg;F",
            "toImperialConversion": "x*1.8+32",
            "toMetricConversion": "(x-32)/1.8",
            "decimalDigits": 1
        },
        {
            "name": "Auto Cool Temperature",
            "type": "number",
            "unit": "&deg;C",
            "imperialUnit": "&deg;F",
            "toImperialConversion": "x*1.8+32",
            "toMetricConversion": "(x-32)/1.8",
            "decimalDigits": 1,
            "controllable": True,
            "minValue": 10,
            "maxValue": 100
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
            "maxValue": 20
        }
    ]
}


def onIoEStateSet(stateName, value):
    global tMax
    global tMin
    global Mode

    if stateName == "Mode":
        Mode = MODES[value]
        if value == MODE_CODE["Off"]:
            turnOffCooling()
            turnOffHeating()
            showMessage("Off")
        elif value == MODE_CODE["Cooling"]:
            turnOffHeating()
            turnOnCooling()
            showMessage("Cooling")
        elif value == MODE_CODE["Heating"]:
            turnOffCooling()
            turnOnHeating()
            showMessage("Heating")
        elif value == MODE_CODE["Auto"]:
            showMessage("Auto")
        else:
            print("Unknown option", value)

    elif stateName == "Auto Cool Temperature":
        tMin = float(value)
    elif stateName == "Auto Heat Temperature":
        tMax = float(value)
    else:
        print("Unknown state", stateName, value)


def IoEUpdateState():
    IoEClient.reportStates([MODE_CODE[Mode], getTemperature(), tMax, tMin])


def IoESetup():
    IoEClient.setup(CONFIG)
    IoEClient.onStateSet(onIoEStateSet)
    IoEUpdateState()


# ==== web
httpClient = RealHTTPClient()
SERVER = 'http://localhost:5000/'


def getISO8601Date():
    current_time = time()

    time_struct = gmtime(current_time)

    iso_8601_date = strftime("%Y-%m-%dT%H:%M:%SZ", time_struct)

    return iso_8601_date


def onHTTPDone(status, data, replyHeader):
    print("Status", status)
    # print(data)
    print("Reply header", replyHeader)


httpClient.onDone(onHTTPDone)


def sendToServer(route, data):
    httpClient.postWithHeader(
        SERVER + route,
        data,
        {
            "Content-Type": "application/json"
        }
    )


def sendTemperatureDataToServer(t):
    temperature_data = {
        "temperature": t,
        "time": getISO8601Date()
    }

    sendToServer({
        "temperature_data": temperature_data
    })


def sendTemperaturesDataToServer(t):
    global temperatures_batch

    temperature_data = {
        "temperature": t,
        "time": getISO8601Date()
    }

    temperatures_batch.append(temperature_data)

    if len(temperatures_batch) == BATCH_LEN:
        sendToServer('batch', {
            "temperatures_batch": temperatures_batch
        })

        temperatures_batch = []

# ==== iot


def showMessage(message):
    customWrite(DISPLAY_PIN, message)
    print(message)


def temperatureToCelsius(t):
    return float(t)*200/(HIGH-LOW)-100


def getTemperature():
    t = analogRead(TEMPERATURE_PIN)
    return temperatureToCelsius(t)


def turnOnHeating():
    global isHeating
    digitalWrite(HAETING_PIN, HIGH)
    isHeating = True


def turnOffHeating():
    global isHeating
    digitalWrite(HAETING_PIN, LOW)
    isHeating = False


def heatingControl(t):
    if t < tMin and not isHeating:
        turnOnHeating()
        showMessage("Heating on")
    if t > tMin and isHeating:
        turnOffHeating()
        showMessage("Heating off")


def turnOnCooling():
    global isCooling
    digitalWrite(COOLING_PIN, HIGH)
    isCooling = True


def turnOffCooling():
    global isCooling
    digitalWrite(COOLING_PIN, LOW)
    isCooling = False


def coolingControl(t):
    if t > tMax and not isCooling:
        turnOnCooling()
        showMessage("Cooling on")
    if t < tMax and isCooling:
        turnOffCooling()
        showMessage("Cooling off")


def init():
    turnOffHeating()
    turnOffCooling()
    IoESetup()


def main():
    while True:
        t = getTemperature()
        if Mode == "Auto":
            showMessage(str(t)+" C")
            heatingControl(t)
            coolingControl(t)
        IoEUpdateState()
        sendTemperaturesDataToServer(t)
        sleep(TIMEOUT)


if __name__ == "__main__":
    init()
    main()
