from gpio import *
from time import *
from ioeclient import IoEClient

TIMEOUT = 4

MODES = {
	'0': 'Off',
	'1': 'Cooling',
	'2': 'Heating',
	'3': 'Auto'
}

MODE_CODE = {
	value: key for key, value in MODES.items()
}

ROOMS = {
	'Room 1':{
		'pins':{
			'heating':0,
			'cooling':1,
			'display':2,
			'temperature':A0
		},
		'isHeating': False,
		'isCooling': False,
		'temperature':{
			'max': 25,
			'min': 18
		},
		'mode': 'Auto'
	},
	'Room 2':{
		'pins':{
			'heating':3,
			'cooling':4,
			'display':5,
			'temperature':A1
		},
		'isHeating': False,
		'isCooling': False,
		'temperature':{
			'max': 28,
			'min': 21
		},
		'mode': 'Auto'
	}
}

ROOM_OPTIONS = dict(zip([str(k) for k in range(len(ROOMS))], ROOMS.keys()))

ROOM_OPTION_CODE = dict(zip(ROOMS.keys(), [str(k) for k in range(len(ROOMS))]))

chosenRoom = [key for key in ROOMS.keys()][0]

# IOeClient
CONFIG = {
	"type": "Thermostat",
	"states": [
    	{
    		"name": "Room",
    		"type": "options",
    		"options": {'0': 'Room 1', '1': 'Room 2'},
    		"controllable": True
    	},
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
	global ROOMS
	global chosenRoom
    
	room = ROOMS[chosenRoom]
    
	if stateName == "Room":
		if value in ROOM_OPTIONS.keys():
   			chosenRoom = ROOM_OPTIONS[value]
   			
   			room = ROOMS[chosenRoom]
		else:
    		print("Unknown option", value)
	elif stateName == "Mode":
		if value in MODES.keys():
			mode = MODES[value]
			
			room['mode'] = mode
 
			if mode == 'Off':
				turnOffCooling(chosenRoom)
				turnOffHeating(chosenRoom)
				displayRoomMessage("Off", chosenRoom)
			elif mode == 'Cooling':
				turnOffHeating(chosenRoom)
				turnOnCooling(chosenRoom)
				displayRoomMessage("Cooling", chosenRoom)
			elif mode == 'Heating':
				turnOffCooling(chosenRoom)
				turnOnHeating(chosenRoom)
				displayRoomMessage("Heating", chosenRoom)
			elif mode == 'Auto':
				displayRoomMessage("Auto", chosenRoom)
		else:
			print("Unknown option", value)
	elif stateName == "Auto Cool Temperature":
		room['temperature']['max'] = float(value)
	elif stateName == "Auto Heat Temperature":
		room['temperature']['min'] = float(value)
	else:
		print("Unknown state", stateName, value)


def IoEUpdateState():
	room = ROOMS[chosenRoom]
	
	IoEClient.reportStates([ROOM_OPTION_CODE[chosenRoom],MODE_CODE[room['mode']],getTemperature(chosenRoom),room['temperature']['max'],room['temperature']['min']])


def IoESetup():
	IoEClient.setup(CONFIG)
	IoEClient.onStateSet(onIoEStateSet)
	IoEUpdateState()
	
def displayMessage(message, pin):
	customWrite(pin, str(message))

def displayRoomMessage(message, room):
	roomDisplayPin = ROOMS[room]['pins']['display']
	
	displayMessage(message, roomDisplayPin)
	
def displayTemperature(t, room):
	displayRoomMessage('{0} temp.:\n{1:.2} C'.format(room, t), room)

def temperatureToCelsius(t):
	return float(t)*200/(HIGH-LOW)-100

def getTemperature(room):
	roomTemperaturePin = ROOMS[room]['pins']['temperature']
	
	t = analogRead(roomTemperaturePin)
	
	return temperatureToCelsius(t)

def turnOnHeating(room):
	roomHeatingPin = ROOMS[room]['pins']['heating']
	
	digitalWrite(roomHeatingPin, HIGH)
	
	ROOMS[room]['isHeating'] = True

def turnOffHeating(room):
	roomHeatingPin = ROOMS[room]['pins']['heating']
	
	digitalWrite(roomHeatingPin, LOW)
	
	ROOMS[room]['isHeating'] = False
	
def heatingControl(t, room):
	isHeating = ROOMS[room]['isHeating']
	
	t_min = ROOMS[room]['temperature']['min']
	
	if t<t_min and not isHeating:
		turnOnHeating(room)
		
		displayRoomMessage("Heating on", room)
	elif t>t_min and isHeating:
		turnOffHeating(room)
		
		displayRoomMessage("Heating off", room)

def turnOnCooling(room):
	roomCoolingPin = ROOMS[room]['pins']['cooling']
	
	digitalWrite(roomCoolingPin, HIGH)
	
	ROOMS[room]['isCooling'] = True

def turnOffCooling(room):
	roomCoolingPin = ROOMS[room]['pins']['cooling']
	
	digitalWrite(roomCoolingPin, LOW)
	
	ROOMS[room]['isCooling'] = False
	
def coolingControl(t, room):
	isCooling = ROOMS[room]['isCooling']
	
	t_max = ROOMS[room]['temperature']['max']
		
	if t>t_max and not isCooling:
		turnOnCooling(room)
		
		displayRoomMessage("Cooling on", room)
	elif t<t_max and isCooling:
		turnOffCooling()
		
		displayRoomMessage("Cooling off", room)
		
def climateControl(t, room):
	heatingControl(t, room)
	
	coolingControl(t, room)
		
def init():
	for room in ROOMS:
		turnOffHeating(room)
		
		turnOffCooling(room)
		
	IoESetup()

def main():
	while True:
		for room in ROOMS:
			t = getTemperature(room)
			
			if ROOMS[room]['mode'] == 'Auto':
				displayTemperature(t, room)
				
				climateControl(t, room)
			
		IoEUpdateState()
		
		sleep(TIMEOUT)

if __name__ == "__main__":
	init()
	
	main()