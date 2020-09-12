########################################################################
# Scare v1.0
# 
# Triggers an animatronic and a whole house strobe effect.
# Author: Adam Lay
########################################################################

# Imports
import RPi.GPIO as GPIO
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
from time import sleep, time, strftime, asctime
from websocket import create_connection
import math
import threading

# Various pins used for effect, using BOARD pin numbering
buttonPin = 12
Relay_Ch1 = 37 # Ch 2 = 38, Ch 3 = 40

# Configuration/State Variables
strobeSceneId = 3
regularSceneId = 5
PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.

# Global Timing Variable
acceptableLaunchTime = time()

# Initialize connection to light console
ws = create_connection("ws://192.168.1.5:9999/qlcplusWS")

# Initialize LCD Display
try:
    mcp = PCF8574_GPIO(PCF8574_address)
except:
    try:
        mcp = PCF8574_GPIO(PCF8574A_address)
    except:
        print ('I2C Address Error !')
        exit(1)
# Create LCD, passing in MCP GPIO adapter.
lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=mcp)

# Setup
def setup():
    # Set the pin numbering
    GPIO.setmode(GPIO.BOARD)

    # Setup pins and relays.
    GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(Relay_Ch1,GPIO.OUT)
    GPIO.output(Relay_Ch1,GPIO.HIGH)
    
    # Event handler
    GPIO.add_event_detect(buttonPin, GPIO.RISING, callback=executeScare, bouncetime=2000)

    # Set "ready to scare" on LCD display.
    mcp.output(3,1)
    lcd.begin(16,2)
    lcd.clear()
    lcd.message(' Ready to scare ' )

    print('Initialized, ready to scare!')

# The primary scare function.
def executeScare (pin):
    global acceptableLaunchTime

    # If we are not currently scaring
    if time() > acceptableLaunchTime:
        print('Scaring in progress..')

        # We don't want to scare again for at least 60 seconds.
        acceptableLaunchTime = time() + 60

        lcd.clear()
        lcd.message('   Scaring...  \nPlease Stand By')

        # Activate relay for animatronic.
        GPIO.output(Relay_Ch1,GPIO.LOW)

        # Send DMX command
        startStrobeScene()

        # Wait 2 seconds
        sleep(2)

        # Turn off relay for animatronic, that should be enough time to trigger.
        GPIO.output(Relay_Ch1,GPIO.HIGH)

        # Wait 15 seconds (how long before we should return lighting to normal)
        sleep(15)

        # Run reset scare function.
        resetScare()
    else:
        print('Attempted to execute scare before acceptable time, try again soon.')

# The reset event.
def resetScare ():

    # Send DMX command to reset.
    stopStrobeScene()

    # Start cooldown
    t1 = threading.Thread(target=cooldown)  
    t1.start() 

    print('Ready to scare again after delay.')

# The cooldown function.
def cooldown ():
    lcd.clear()
    lcd.setCursor(0,0)
    lcd.message('Scare ready in:')

    while time() < acceptableLaunchTime:
        remainingSecs = str(math.ceil(acceptableLaunchTime - time())).zfill(2)
        lcd.setCursor(0,1)
        lcd.message('   ' + str(remainingSecs)+' seconds')
        sleep(1)
    
    lcd.clear()
    lcd.message(' Ready to scare ' )

def startStrobeScene():
    print("Sending light command via websocket")
    # Stop Existing
    ws.send('QLC+API|setFunctionStatus|' + str(regularSceneId) + '|0')
    ws.send('QLC+API|setFunctionStatus|' + str(strobeSceneId) + '|1')

def stopStrobeScene():
    print("Sending light command via websocket")
    # Stop Existing
    ws.send('QLC+API|setFunctionStatus|' + str(strobeSceneId) + '|0')
    ws.send('QLC+API|setFunctionStatus|' + str(regularSceneId) + '|1')

# Main Program Loop
try:
    setup()
    while True : sleep(0.5)
except:
    lcd.clear()
    GPIO.cleanup()      
