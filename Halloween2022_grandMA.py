########################################################################
# Scare v3.0 - Halloween 2022
#
# Triggers two animatronic creatures and a whole house strobe effect.
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
Relay_Ch2 = 38

# Configuration/State Variables
scaringPorch = False
scaringLawn = False
grandMAIP = "192.168.1.5"
oscPort = 64300
oscClient = SimpleUDPClient(grandMAIP, oscPort)

# Ambient Music Paths
ambientMusicPath = "/home/pi/Documents/halloween/sounds/HalloweenAmbiance.ogg"

# Scare Sound Effect Paths
porchScareSoundPath = "/home/pi/Documents/halloween/sounds/PorchScare.ogg"
lawnScareSoundPath = "/home/pi/Documents/halloween/sounds/JumpScare.ogg"
thunderSoundPath = "/home/pi/Documents/halloween/sounds/thunder.ogg"

# General Sound Effect Paths
s1Path = "/home/pi/Documents/halloween/sounds/sound-effects/AlienScream-s1.ogg"
s2Path = "/home/pi/Documents/halloween/sounds/sound-effects/BassBuild-s2.ogg"
s3Path = "/home/pi/Documents/halloween/sounds/sound-effects/BoneBreak-s3.ogg"
s4Path = "/home/pi/Documents/halloween/sounds/sound-effects/DraconicLaugh-s7.ogg"
s5Path = "/home/pi/Documents/halloween/sounds/sound-effects/EvilLaugh-s8.ogg"
s6Path = "/home/pi/Documents/halloween/sounds/sound-effects/FemaleScream-s9.ogg"
s7Path = "/home/pi/Documents/halloween/sounds/sound-effects/GhostWhoosh-s11.ogg"
s8Path = "/home/pi/Documents/halloween/sounds/sound-effects/MonsterRoar-s12.ogg"
s9Path = "/home/pi/Documents/halloween/sounds/sound-effects/OrcRoar-s13.ogg"
s10Path = "/home/pi/Documents/halloween/sounds/sound-effects/TensionChord-s15.ogg"
s11Path = "/home/pi/Documents/halloween/sounds/sound-effects/ViolinChord-s16.ogg"

# Voice Sound Effect Paths
v1Path = "/home/pi/Documents/halloween/sounds/sound-effects/Voice_HappyHalloween-v1.ogg"
v2Path = "/home/pi/Documents/halloween/sounds/sound-effects/Voice_CoolCostume-v2.ogg"
v3Path = "/home/pi/Documents/halloween/sounds/sound-effects/Voice_CoolCostumes-v3.ogg"
v4Path = "/home/pi/Documents/halloween/sounds/sound-effects/Voice_ISeeYouStandingThere-v4.ogg"
v5Path = "/home/pi/Documents/halloween/sounds/sound-effects/Voice_GoAheadRingDoorbell-v5.ogg"
v6Path = "/home/pi/Documents/halloween/sounds/sound-effects/Voice_ComeBack-v6.ogg"

# Initialize music mixer.
pygame.mixer.init()

# Load ambient music into memory
ambientMusic = pygame.mixer.Sound(ambientMusicPath)
ambientMusicVolume = 0.3

# Load scare sounds into memory
porchScareSound = pygame.mixer.Sound(porchScareSoundPath)
lawnScareSound = pygame.mixer.Sound(lawnScareSoundPath)
thunderSound = pygame.mixer.Sound(thunderSoundPath)

# Load sound effects into memory
s1 = pygame.mixer.Sound(s1Path)
s2 = pygame.mixer.Sound(s2Path)
s3 = pygame.mixer.Sound(s3Path)
s4 = pygame.mixer.Sound(s4Path)
s5 = pygame.mixer.Sound(s5Path)
s6 = pygame.mixer.Sound(s6Path)
s7 = pygame.mixer.Sound(s7Path)
s8 = pygame.mixer.Sound(s8Path)
s9 = pygame.mixer.Sound(s9Path)
s10 = pygame.mixer.Sound(s10Path)
s11 = pygame.mixer.Sound(s11Path)

# Load voice effects into memory
v1 = pygame.mixer.Sound(v1Path)
v2 = pygame.mixer.Sound(v2Path)
v3 = pygame.mixer.Sound(v3Path)
v4 = pygame.mixer.Sound(v4Path)
v5 = pygame.mixer.Sound(v5Path)
v6 = pygame.mixer.Sound(v6Path)

# Setup

# This function intializes the pi board


def setup():
    # Set the pin numbering
    GPIO.setmode(GPIO.BOARD)

    # Setup pins and relays.
    GPIO.setup(Relay_Ch1, GPIO.OUT)
    GPIO.output(Relay_Ch1, GPIO.HIGH)
    GPIO.setup(Relay_Ch2, GPIO.OUT)
    GPIO.output(Relay_Ch2, GPIO.HIGH)

    # Start scare music
    playAmbientMusic()

    # Start light show
    sendOSCCommand("/gma3/cmd", "On Exec 202")

    # Return our initialized message.
    print('>> Initialization complete.')

# Play the ambient music


def playAmbientMusic():
    global ambientMusic
    print('>> Starting ambient music.')
    # Set the volume and play indefinitely.
    ambientMusic.set_volume(ambientMusicVolume)
    ambientMusic.play(loops=-1)

# Play a thunder sound effect and strobe.


def thunder():
    global thunderSound
    print('>> THUNDERING')
    thunderSound.set_volume(0.6)
    thunderSound.play()
    sendOSCCommand("/gma3/cmd", "On Exec 205")

def playSoundEffect(id):
    # Play the sound effect.
    id.play()

def muteAmbientMusic():
    ambientMusic.set_volume(0)

def unmuteAmbientMusic():
    ambientMusic.set_volume(ambientMusicVolume)

# The primary scare function.


def executeScare(zone):
    global scaringPorch
    global scaringLawn
    global ambientMusic

    if zone == 'porch':
        if scaringPorch is False:
            print('>>> SCARING (PORCH) IN PROGRESS <<<')
            # Start scare sequence
            t1 = threading.Thread(target=porchScareSequence)
            t1.start()
        else:
            print('>> ALERT: Already running scare sequence (PORCH), try again in a minute.')
    elif zone == 'lawn':
        if scaringLawn is False:
            print('>>> SCARING (LAWN) IN PROGRESS <<<')
            # Start scare sequence
            t2 = threading.Thread(target=lawnScareSequence)
            t2.start()

# The LAWN scare sequence


def porchScareSequence():
    global scaringPorch
    global porchScareSound
    global ambientMusic

    # Fade out the ambient music
    ambientMusic.fadeout(2000)

    # Set our variable to prevent another command.
    scaringPorch = True

    # Wait for music to fade out
    sleep(1)

    # Activate relay for animatronic.
    GPIO.output(Relay_Ch1, GPIO.LOW)

    # Wait a second before triggering the strobe.
    sleep(1)

    # Play the sound effect
    porchScareSound.play()

    # Wait 0.2 seconds before triggering strobe scene.
    sleep(0.2)

    # Send OSC command to light console.
    sendOSCCommand("/gma3/cmd", "On Exec 201")

    # Wait a second before turning the relay off.
    sleep(1)

    # Turn off relay for animatronic, that should be enough time to trigger.
    GPIO.output(Relay_Ch1, GPIO.HIGH)

    # Start our ambient music again.
    ambientMusic.play(loops=-1)

    # Wait 21 seconds (how long before we should return lighting to normal)
    sleep(49)

    # Run reset scare function.
    # Ready for next scare
    scaringPorch = False

    print('>>> READY TO SCARE! <<<')

def lawnScareSequence():
    global scaringLawn
    global lawnScareSound

    scaringLawn = True

    # Activate relay for animatronic.
    GPIO.output(Relay_Ch2, GPIO.LOW)

    # Wait a second before triggering the strobe.
    sleep(0.8)

    # Play the sound effect
    lawnScareSound.play()

    sleep(0.2)

    # Send OSC command to light console.
    sendOSCCommand("/gma3/cmd", "On Exec 201")

    # Wait a second before turning the relay off.
    sleep(1)

    # Turn off relay for animatronic, that should be enough time to trigger.
    GPIO.output(Relay_Ch2, GPIO.HIGH)

    # Wait 21 seconds (how long before we should return lighting to normal)
    sleep(21)

    # Run reset scare function.
    # Ready for next scare
    scaringLawn = False

    print('>>> Lawn scare complete. Ready to go again. <<<')


# Send the OSC command to our lighting console.


def sendOSCCommand(address, command):
    print(">> Sending light command via OSC to GMA3 console: " + command)
    try:
        oscClient.send_message(address, command)
    except:
        print('>> ALERT: Unable to send OSC command to light console.')


# def call_repeatedly(interval, func, *args):
#     stopped = threading.Event()

#     def loop():
#         while not stopped.wait(interval):  # the first call is in `interval` secs
#             func(*args)
#     threading.Thread(target=loop).start()
#     return stopped.set

# Initialize HTTP server and listen for request.


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/porch':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> HTTP request received for PORCH, requesting scare sequence.')
            executeScare('porch')
        elif self.path == '/lawn':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> HTTP request received for LAWN, requesting scare sequence.')
            executeScare('lawn')
        elif self.path == '/lightning':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> HTTP request received for LIGHTNING, requesting scare sequence.')
            thunder()
        elif self.path == '/s1':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S1 triggered.')
            playSoundEffect(s1)
        elif self.path == '/s2':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S2 triggered.')
            playSoundEffect(s2)
        elif self.path == '/s3':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S3 triggered.')
            playSoundEffect(s3)
        elif self.path == '/s4':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S4 triggered.')
            playSoundEffect(s4)
        elif self.path == '/s5':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S5 triggered.')
            playSoundEffect(s5)
        elif self.path == '/s6':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S6 triggered.')
            playSoundEffect(s6)
        elif self.path == '/s7':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S7 triggered.')
            playSoundEffect(s7)
        elif self.path == '/s8':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S8 triggered.')
            playSoundEffect(s8)
        elif self.path == '/s9':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S9 triggered.')
            playSoundEffect(s9)
        elif self.path == '/s10':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S10 triggered.')
            playSoundEffect(s10)
        elif self.path == '/s11':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Sound effect S11 triggered.')
            playSoundEffect(s11)
        elif self.path == '/v1':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Voice effect V1 triggered.')
            playSoundEffect(v1)
        elif self.path == '/v2':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Voice effect V2 triggered.')
            playSoundEffect(v2)
        elif self.path == '/v3':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Voice effect V3 triggered.')
            playSoundEffect(v3)
        elif self.path == '/v4':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Voice effect V4 triggered.')
            playSoundEffect(v4)
        elif self.path == '/v5':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Voice effect V5 triggered.')
            playSoundEffect(v5)
        elif self.path == '/v6':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Voice effect V6 triggered.')
            playSoundEffect(v6)
        elif self.path == '/ambient-unmute':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Ambient music unmuted.')
            unmuteAmbientMusic()
        elif self.path == '/ambient-mute':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
            print('>> Ambient music muted.')
            muteAmbientMusic()
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
