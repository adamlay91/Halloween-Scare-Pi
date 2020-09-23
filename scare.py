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
from time import sleep
from websocket import create_connection
import threading

# Various pins used for effect, using BOARD pin numbering
buttonPin = 12
Relay_Ch1 = 37 # Ch 2 = 38, Ch 3 = 40
greenLedPin = 32
redLedPin = 22

# Configuration/State Variables
scaring = False
strobeSceneId = 29
regularSceneId = 45
PCF8574_address = 0x27  # I2C address of the PCF8574 chip.
PCF8574A_address = 0x3F  # I2C address of the PCF8574A chip.

# Initialize connection to light console
try:
    ws = create_connection("ws://192.168.1.5:9999/qlcplusWS")
except:
    print('Websocket offline.')

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
    GPIO.setup(greenLedPin, GPIO.OUT)
    GPIO.output(greenLedPin, GPIO.HIGH)
    GPIO.setup(redLedPin, GPIO.OUT)
    GPIO.output(redLedPin, GPIO.LOW)
    
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
    global scaring

    # If we are not currently scaring
    if scaring is False:

        # We don't want to scare again until the process is complete.
        scaring = True

        print('Scaring in progress..')

         # Start scare sequence
        t1 = threading.Thread(target=scareSequence)  
        t1.start() 
        
    else:
        print('Already running scare sequence, try again in a minute.')

def scareSequence():
    global scaring

    # Update LCD message
    lcd.clear()
    lcd.message('   Scaring...  \nPlease Stand By')

    # Start scare sequence
    t2 = threading.Thread(target=showBusyLight)  
    t2.start() 

    # Activate relay for animatronic.
    GPIO.output(Relay_Ch1,GPIO.LOW)

    #Wait a second before triggering the strobe.
    sleep(1)

    # Send DMX command
    startStrobeScene()

    # Wait a second before turning the relay off.
    sleep(1)

    # Turn off relay for animatronic, that should be enough time to trigger.
    GPIO.output(Relay_Ch1,GPIO.HIGH)

    # Wait 25 seconds (how long before we should return lighting to normal)
    sleep(20)

    # Run reset scare function.
    resetScare()

# The reset event.
def resetScare ():
    global scaring

    # Send DMX command to reset.
    stopStrobeScene()

    # Ready for next scare
    scaring = False

    # Update the LCD screen
    lcd.clear()
    lcd.message(' Ready to scare ')

    print('Ready to scare again.')

def startStrobeScene():
    print("Sending light command via websocket")
    # Stop Existing
    try:
        ws.send('QLC+API|setFunctionStatus|' + str(regularSceneId) + '|0')
        ws.send('QLC+API|setFunctionStatus|' + str(strobeSceneId) + '|1')
    except:
        print('Unable to send command to light console.')

def stopStrobeScene():
    print("Sending light command via websocket")
    # Stop Existing
    try:
        ws.send('QLC+API|setFunctionStatus|' + str(strobeSceneId) + '|0')
        ws.send('QLC+API|setFunctionStatus|' + str(regularSceneId) + '|1')
    except:
        print('Unable to send command to light console.')

def showBusyLight():

    GPIO.output(greenLedPin, GPIO.LOW)

    while scaring is True:
        GPIO.output(redLedPin, GPIO.HIGH)
        sleep(0.1)
        GPIO.output(redLedPin, GPIO.LOW)
        sleep(0.1)
    
    GPIO.output(greenLedPin, GPIO.HIGH)

# Main Program Loop
try:
    setup()
    while True : sleep(0.5)
except:
    lcd.clear()
    GPIO.cleanup()      
