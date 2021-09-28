########################################################################
# Scare v2.0 - Halloween 2021
#
# Triggers an animatronic creature and a whole house strobe effect.
# Author: Adam Lay
########################################################################

# Imports

# GPIO Control
import RPi.GPIO as GPIO
from time import sleep
import threading

# HTTP Server for scare requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# Pygame for Audio Support
import pygame

# PythonOSC for sending OSC commands to grandMA light console
from pythonosc.udp_client import SimpleUDPClient


# Global Config Variables

# Various pins used for effect, using BOARD pin numbering
Relay_Ch1 = 37  # Ch 2 = 38, Ch 3 = 40

# Configuration/State Variables
scaring = False
grandMAIP = "192.168.1.5"
oscPort = 64300
oscClient = SimpleUDPClient(grandMAIP, oscPort)

# Music variables
ambientMusicPath = "/home/pi/Documents/halloween/sounds/HalloweenAmbiance.ogg"
scareMusicPath = "/home/pi/Documents/halloween/sounds/JumpScare.ogg"
thunderSoundPath = "/home/pi/Documents/halloween/sounds/thunder.ogg"
ambientMusicLevel = -3000

# Initialize music mixer.
pygame.mixer.init()
scareSound = pygame.mixer.Sound(scareMusicPath)
ambientMusic = pygame.mixer.Sound(ambientMusicPath)
thunderSound = pygame.mixer.Sound(thunderSoundPath)

# Setup

# This function intializes the pi board


def setup():
    # Set the pin numbering
    GPIO.setmode(GPIO.BOARD)

    # Setup pins and relays.
    GPIO.setup(Relay_Ch1, GPIO.OUT)
    GPIO.output(Relay_Ch1, GPIO.HIGH)

    # Start scare music
    playAmbientMusic()

    # Start the timed thunder/lighting.
    startTimedThunder()

    # Start light show
    sendOSCCommand("/gma3/cmd", "On Exec 202")

    # Return our initialized message.
    print('>> Initialization complete.')

# Play the ambient music


def playAmbientMusic():
    global ambientMusic
    print('>> Starting ambient music.')
    # Set the volume and play indefinitely.
    ambientMusic.set_volume(0.5)
    ambientMusic.play(loops=-1)

# Start the interval timer, thunder every 2 minutes.


def startTimedThunder():
    global thunderInterval
    thunderInterval = call_repeatedly(120, thunder)

# Stop the interval timer


def stopTimedThunder():
    global thunderInterval
    thunderInterval()

# Play a thunder sound effect and strobe.


def thunder():
    global thunderSound
    print('>> THUNDERING')
    thunderSound.set_volume(0.6)
    thunderSound.play()
    sendOSCCommand("/gma3/cmd", "On Exec 205")


# The primary scare function.


def executeScare():
    global scaring
    global ambientMusic

    # If we are not currently scaring
    if scaring is False:

        # We don't want to scare again until the process is complete.
        scaring = True

        print('>>> SCARING IN PROGRESS <<<')

        # Fade out the ambient music
        ambientMusic.fadeout(3000)

        # Stop our timed thunder
        stopTimedThunder()

        # Start scare sequence
        t1 = threading.Thread(target=scareSequence)
        t1.start()

    else:
        print('>> ALERT: Already running scare sequence, try again in a minute.')

# The scare sequence


def scareSequence():
    global scaring
    global scareSound

    # Wait for music to fade out
    sleep(2)

    # Activate relay for animatronic.
    GPIO.output(Relay_Ch1, GPIO.LOW)

    # Wait a second before triggering the strobe.
    sleep(1)

    # Play the sound effect
    scareSound.play()

    sleep(0.3)

    # Send OSC command to light console.
    sendOSCCommand("/gma3/cmd", "On Exec 201")

    # Wait a second before turning the relay off.
    sleep(1)

    # Turn off relay for animatronic, that should be enough time to trigger.
    GPIO.output(Relay_Ch1, GPIO.HIGH)

    # Wait 21 seconds (how long before we should return lighting to normal)
    sleep(21)

    # Run reset scare function.
    resetScare()

# The reset event.


def resetScare():
    global scaring
    global ambientMusic

    # Ready for next scare
    scaring = False

    # Start our ambient music again.
    ambientMusic.play(loops=-1)

    # Start our timed thunder again.
    startTimedThunder()

    print('>>> READY TO SCARE! <<<')

# Send the OSC command to our lighting console.


def sendOSCCommand(address, command):
    print(">> Sending light command via OSC to GMA3 console: " + command)
    try:
        oscClient.send_message(address, command)
    except:
        print('>> ALERT: Unable to send OSC command to light console.')


def call_repeatedly(interval, func, *args):
    stopped = threading.Event()

    def loop():
        while not stopped.wait(interval):  # the first call is in `interval` secs
            func(*args)
    threading.Thread(target=loop).start()
    return stopped.set

# Initialize HTTP server and listen for request.


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/scare':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> HTTP request received, requesting scare sequence.')
            executeScare()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Bad request')


# Main Program Loop
try:
    setup()
    httpd = HTTPServer(("", 8080), SimpleHTTPRequestHandler)
    print('>>> READY TO SCARE! <<<')
    httpd.serve_forever()
except:
    GPIO.cleanup()
